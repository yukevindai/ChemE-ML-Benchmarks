"""Evaluate exact official row identities; never trust submitted metric values."""
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from .common import (canonical, csv_bytes, csv_frame, digest, fields, manifest_files,
                     new_directory, read_json, software, source_digest, text, verify_files, write_json)
from .metrics import regression_metrics
from .models import GRIDS, model_pipeline
from .prepare import load_prepared


def group_ids(frame, columns):
    # Same transitive grouping semantics as SciSplit: sharing ANY identity joins units.
    parent = list(range(len(frame)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for col in columns:
        first = {}
        for i, value in enumerate(frame[col].astype(str)):
            if value in first:
                parent[root(i)] = root(first[value])
            else:
                first[value] = i
    return np.array([str(root(i)) for i in range(len(frame))])


def score_predictions(spec, frame, frozen, raw):
    predictions = csv_frame(raw)
    if list(predictions) != ["row_id", "partition", "prediction"]:
        raise ValueError("Predictions require row_id, partition, prediction columns in that order")
    if predictions["row_id"].duplicated().any():
        raise ValueError("Duplicate prediction row IDs")
    expected = [a for a in frozen["assignments"] if a["partition"] in {"validation", "test"}]
    expected_map = {a["row_id"]: a["partition"] for a in expected}
    submitted_map = dict(zip(predictions["row_id"], predictions["partition"]))
    if submitted_map != expected_map:
        raise ValueError("Predictions must cover every official validation/test row exactly, with correct partitions")
    values = pd.to_numeric(predictions["prediction"], errors="coerce")
    if not np.isfinite(values).all():
        raise ValueError("Predictions must be finite numbers")
    indexed = dict(zip(predictions["row_id"], values))
    labels = np.array([a["partition"] for a in frozen["assignments"]])
    row_ids = frame[spec["data"]["row_id"]].astype(str)
    groups = group_ids(frame, spec["independence"]["columns"])
    result = {}
    for partition in ("validation", "test"):
        selected = labels == partition
        result[partition] = regression_metrics(frame.loc[selected, spec["target"]],
            [indexed[r] for r in row_ids[selected]], groups[selected])
    return result


def write_run(prepared, destination, predictions, method):
    spec, frame, frozen, manifest = load_prepared(prepared)
    fields(method, {"name", "seed", "origin", "code_reference", "training_description", "parameters", "validation_search"})
    for k in ("name", "code_reference", "training_description"):
        text(method[k], k)
    if method["origin"] not in {"builtin", "external"} or method["seed"] not in spec["model_seeds"] or type(method["seed"]) is not int:
        raise ValueError("Method must declare an allowed seed and origin")
    if not isinstance(method["parameters"], dict) or not isinstance(method["validation_search"], list):
        raise ValueError("Method parameters/search must be JSON object/list")
    metrics = score_predictions(spec, frame, frozen, predictions)
    record = {"schema_version": "1.0", "benchmark_id": manifest["benchmark_id"], "method": method,
              "metrics": metrics, "prediction_sha256": digest(predictions), "software": software(),
              "verification_scope": "Predictions and scores verified against official data/partitions. Training provenance is a declaration; public test labels cannot be secured by local software."}
    record["run_id"] = "run_" + digest(canonical(record))
    with new_directory(destination) as out:
        (out / "predictions.csv").write_bytes(predictions)
        write_json(out / "run.json", record)
        write_json(out / "manifest.json", {"files": manifest_files(out), "run_id": record["run_id"]})
    return record


def run_baseline(prepared, name, destination, seed=0):
    spec, frame, frozen, _ = load_prepared(prepared)
    if name not in GRIDS or type(seed) is not int or seed not in spec["model_seeds"]:
        raise ValueError("Unknown baseline or seed outside benchmark protocol")
    features = spec["features"]["numeric"] + spec["features"]["categorical"]
    labels = np.array([a["partition"] for a in frozen["assignments"]])
    train, validation = labels == "train", labels == "validation"
    groups = group_ids(frame, spec["independence"]["columns"])
    candidates, fitted = [], []
    with threadpool_limits(limits=1):
        for params in GRIDS[name]:
            pipeline = model_pipeline(name, params, spec["features"], seed)
            pipeline.fit(frame.loc[train, features], frame.loc[train, spec["target"]])
            prediction = pipeline.predict(frame.loc[validation, features])
            measured = regression_metrics(frame.loc[validation, spec["target"]], prediction, groups[validation], bootstrap=100)
            candidates.append({"parameters": params, "validation_primary": measured[spec["primary_metric"]]})
            fitted.append(pipeline)
        best = min(range(len(candidates)), key=lambda i: (candidates[i]["validation_primary"], i))
        # Test predictions are made only after validation selects the candidate.
        selected = labels != "train"
        prediction = fitted[best].predict(frame.loc[selected, features])
    output = pd.DataFrame({"row_id": frame.loc[selected, spec["data"]["row_id"]], "partition": labels[selected], "prediction": prediction})
    method = {"name": name, "seed": seed, "origin": "builtin", "code_reference": "cheme-ml-benchmarks:0.1.0:sha256:" + source_digest(Path(__file__).parent),
              "parameters": candidates[best]["parameters"], "validation_search": candidates,
              "training_description": "Protocol preprocessing fit on train only; fixed grid selected on validation primary metric; no train+validation refit; one selected model evaluated on test."}
    return write_run(prepared, destination, csv_bytes(output), method)


def submit(prepared, predictions_path, method_path, destination):
    method = read_json(method_path)
    if method.get("origin") != "external":
        raise ValueError("User submissions must declare external origin")
    return write_run(prepared, destination, Path(predictions_path).read_bytes(), method)


def load_run(prepared, directory):
    spec, frame, frozen, benchmark = load_prepared(prepared)
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    if set(manifest["files"]) != {"run.json", "predictions.csv"}:
        raise ValueError("Run manifest must cover exact protocol files")
    verify_files(directory, manifest)
    record = read_json(directory / "run.json")
    if "run_" + digest(canonical({k: v for k, v in record.items() if k != "run_id"})) != record["run_id"] or manifest["run_id"] != record["run_id"]:
        raise ValueError("Run identity mismatch")
    if record["benchmark_id"] != benchmark["benchmark_id"]:
        raise ValueError("Cannot compare different datasets, task cards, preprocessing protocols, or partitions")
    raw = (directory / "predictions.csv").read_bytes()
    if digest(raw) != record["prediction_sha256"] or score_predictions(spec, frame, frozen, raw) != record["metrics"]:
        raise ValueError("Recorded scores do not match submitted predictions")
    return record
