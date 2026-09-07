"""Versioned scientific task cards; never infer scientific identity from row numbers."""
import re
from pathlib import Path

import numpy as np
import pandas as pd
from chemdata_auditor import AuditConfig, SplitConfig

from .common import csv_frame, digest, fields, integer, names, read_json, safe_path, text

DOMAINS = {"batteries", "electrolytes", "adsorption", "catalysis", "separations", "thermodynamics", "transport", "materials", "process_optimization"}


def validate_spec(spec):
    fields(spec, {"schema_version", "id", "version", "title", "domain", "data_kind", "task", "data", "features", "target", "units",
                  "source", "independence", "generalization", "limitations", "split", "partitions", "audit", "accepted_warnings", "model_seeds", "primary_metric", "protocol"})
    if spec["schema_version"] != "1.0" or spec["protocol"] != "cheme-tabular-v1":
        raise ValueError("Unsupported benchmark schema or protocol")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]+", text(spec["id"], "id")):
        raise ValueError("Benchmark ID must be a lowercase slug")
    for key in ("version", "title"):
        text(spec[key], key)
    if spec["domain"] not in DOMAINS or spec["data_kind"] not in {"empirical", "synthetic"}:
        raise ValueError("Unknown domain or data_kind")
    if spec["task"] != "regression" or spec["primary_metric"] not in {"mae", "rmse", "group_mae", "group_rmse"}:
        raise ValueError("This protocol supports scalar regression and an explicit error metric")
    fields(spec["features"], {"numeric", "categorical"})
    numeric = names(spec["features"]["numeric"], "numeric features", empty=True)
    categorical = names(spec["features"]["categorical"], "categorical features", empty=True)
    if not numeric + categorical or set(numeric) & set(categorical):
        raise ValueError("Features must be nonempty and disjoint by type")
    text(spec["target"], "target")
    fields(spec["data"], {"path", "sha256", "row_id", "rows"})
    integer(spec["data"]["rows"], "rows", 3)
    text(spec["data"]["row_id"], "row_id")
    for obj in (spec["data"], spec["partitions"]):
        if not isinstance(obj.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", obj["sha256"]):
            raise ValueError("Data and partitions require full SHA-256 digests")
    fields(spec["partitions"], {"path", "sha256"})
    if not isinstance(spec["units"], dict) or set(spec["units"]) != set(numeric + [spec["target"]]):
        raise ValueError("Units must be declared for every numeric feature and target")
    for value in spec["units"].values():
        text(value, "unit")
    fields(spec["source"], {"url", "citation", "license", "retrieved", "raw_sha256", "transformations"})
    for value in spec["source"].values():
        text(value, "source field")
    fields(spec["independence"], {"columns", "unit", "status", "rationale"})
    groups = names(spec["independence"]["columns"], "independence columns")
    if spec["independence"]["status"] not in {"documented", "proxy", "synthetic"}:
        raise ValueError("Independence status must be documented, proxy, or synthetic")
    if spec["data_kind"] == "empirical" and spec["independence"]["status"] == "synthetic":
        raise ValueError("Empirical tasks cannot declare synthetic independence")
    for key in ("unit", "rationale"):
        text(spec["independence"][key], key)
    fields(spec["generalization"], {"supports", "does_not_establish"})
    for value in spec["generalization"].values():
        text(value, "generalization")
    names(spec["limitations"], "limitations")
    forbidden = {spec["target"], spec["data"]["row_id"], *groups}
    if forbidden & set(numeric + categorical):
        raise ValueError("Targets, row identifiers and independence identifiers cannot be model features")
    if spec["target"] in groups or spec["target"] == spec["data"]["row_id"]:
        raise ValueError("Target cannot define independent units or row identity")
    split = SplitConfig(**spec["split"])
    if split.allow_target_in_split or spec["target"] in (split.columns + split.group_columns + list(split.group_near_duplicates)):
        raise ValueError("Official partitions cannot condition on target values")
    if not set(groups) <= set(split.group_columns):
        raise ValueError("SciSplit must preserve every declared independent-unit group")
    if split.target_column != spec["target"]:
        raise ValueError("SciSplit must explicitly declare the benchmark target")
    audit = AuditConfig(**spec["audit"])
    if audit.target_column != spec["target"] or set(audit.feature_columns) != set(numeric + categorical):
        raise ValueError("Auditor must inspect the exact target and feature declaration")
    if not isinstance(spec["accepted_warnings"], dict):
        raise ValueError("accepted_warnings must map finding codes to scientific justifications")
    for k, v in spec["accepted_warnings"].items():
        text(k, "warning code")
        text(v, "warning justification")
    seeds = spec["model_seeds"]
    if not isinstance(seeds, list) or not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("model_seeds must be unique and nonempty")
    for seed in seeds:
        integer(seed, "model seed")
        if seed >= 2**32:
            raise ValueError("Model seed exceeds supported range")
    return spec


def load_data(spec, raw):
    if digest(raw) != spec["data"]["sha256"]:
        raise ValueError("Dataset snapshot digest mismatch")
    frame = csv_frame(raw)
    if len(frame) != spec["data"]["rows"]:
        raise ValueError("Dataset row count mismatch")
    required = set(spec["features"]["numeric"] + spec["features"]["categorical"] + [spec["target"], spec["data"]["row_id"]] + spec["independence"]["columns"])
    if not required <= set(frame.columns):
        raise ValueError(f"Dataset lacks required columns: {sorted(required - set(frame.columns))}")
    rid = frame[spec["data"]["row_id"]]
    if rid.duplicated().any() or rid.str.strip().eq("").any():
        raise ValueError("Row IDs must be nonblank and unique")
    for col in spec["independence"]["columns"]:
        if frame[col].str.strip().eq("").any():
            raise ValueError("Independent-unit metadata cannot be missing")
    for col in spec["features"]["numeric"] + [spec["target"]]:
        blank = frame[col].str.strip().eq("")
        converted = pd.to_numeric(frame[col].mask(blank), errors="coerce")
        if (converted.isna() & ~blank).any() or np.isinf(converted).any():
            raise ValueError(f"Invalid or infinite numeric data in {col}")
        if col == spec["target"] and converted.isna().any():
            raise ValueError("Targets cannot be missing or imputed")
        frame[col] = converted.astype(float)
    for col in spec["features"]["categorical"]:
        frame[col] = frame[col].mask(frame[col].str.strip().eq(""), np.nan)
    return frame


def load_benchmark(path):
    path = Path(path)
    spec = validate_spec(read_json(path))
    raw = safe_path(path.parent, spec["data"]["path"]).read_bytes()
    frozen_raw = safe_path(path.parent, spec["partitions"]["path"]).read_bytes()
    if digest(frozen_raw) != spec["partitions"]["sha256"]:
        raise ValueError("Official partition digest mismatch")
    frozen = read_json(safe_path(path.parent, spec["partitions"]["path"]))
    return spec, load_data(spec, raw), raw, frozen, frozen_raw
