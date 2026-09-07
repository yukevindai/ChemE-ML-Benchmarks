import copy
import json

import numpy as np
import pytest

from cheme_benchmarks import leaderboard, load_prepared, run_baseline
from cheme_benchmarks.cli import main
from cheme_benchmarks.common import canonical, csv_bytes, csv_frame, digest, read_json
from cheme_benchmarks.evaluate import load_run, score_predictions, submit


@pytest.mark.parametrize("model", ["mean", "ridge", "random_forest", "hist_gradient_boosting"])
def test_all_baselines_produce_recomputable_scores(prepared, tmp_path, model):
    out = tmp_path / model
    result = run_baseline(prepared, model, out)
    assert result == load_run(prepared, out)
    spec, frame, frozen, _ = load_prepared(prepared)
    assert result["metrics"] == score_predictions(spec, frame, frozen, (out / "predictions.csv").read_bytes())
    if model == "mean":
        train = [a["partition"] == "train" for a in frozen["assignments"]]
        pred = csv_frame((out / "predictions.csv").read_bytes())
        assert np.allclose(pred.prediction.astype(float), frame.loc[train, spec["target"]].mean())


def test_predictions_require_exact_ids_and_finite_values(prepared, tmp_path):
    out = tmp_path / "run"
    run_baseline(prepared, "mean", out)
    spec, frame, frozen, _ = load_prepared(prepared)
    predictions = csv_frame((out / "predictions.csv").read_bytes())
    for mutation in ("missing", "duplicate", "wrong_partition", "nan"):
        changed = predictions.copy()
        if mutation == "missing":
            changed = changed.iloc[1:]
        elif mutation == "duplicate":
            changed.loc[1, "row_id"] = changed.loc[0, "row_id"]
        elif mutation == "wrong_partition":
            changed.loc[0, "partition"] = "train"
        else:
            changed.loc[0, "prediction"] = "NaN"
        with pytest.raises(ValueError):
            score_predictions(spec, frame, frozen, csv_bytes(changed))
    shuffled = predictions.sample(frac=1, random_state=4)
    assert score_predictions(spec, frame, frozen, csv_bytes(shuffled)) == score_predictions(spec, frame, frozen, csv_bytes(predictions))


def test_leaderboard_requires_complete_seeds_and_rejects_duplicates(prepared, tmp_path):
    runs = []
    for seed in (0, 1, 2):
        out = tmp_path / f"run-{seed}"
        run_baseline(prepared, "mean", out, seed)
        runs.append(out)
    assert leaderboard(prepared, runs[:1])["entries"][0]["rank"] is None
    report = leaderboard(prepared, runs, tmp_path / "board")
    assert report["entries"][0]["rank"] == 1
    assert report["entries"][0]["test_primary_seed_std"] == 0
    with pytest.raises(ValueError, match="Duplicate"):
        leaderboard(prepared, runs + runs[:1])


def test_external_submission_and_metric_forgery(prepared, tmp_path):
    out = tmp_path / "baseline"
    result = run_baseline(prepared, "mean", out)
    method = dict(result["method"], name="external-example", origin="external", code_reference="https://example.org/commit/123")
    method_path = tmp_path / "method.json"
    method_path.write_text(json.dumps(method))
    submit(prepared, out / "predictions.csv", method_path, tmp_path / "external")
    assert load_run(prepared, tmp_path / "external")["method"]["origin"] == "external"
    record = read_json(out / "run.json")
    record["metrics"]["test"]["mae"] = 0.0
    record["run_id"] = "run_" + digest(canonical({k:v for k,v in record.items() if k != "run_id"}))
    (out / "run.json").write_text(json.dumps(record))
    manifest = read_json(out / "manifest.json")
    manifest["run_id"] = record["run_id"]
    manifest["files"]["run.json"] = digest((out / "run.json").read_bytes())
    (out / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="scores"):
        load_run(prepared, out)


def test_cli_run_and_no_overwrite(prepared, tmp_path, capsys):
    argv = ["run", str(prepared), "--model", "mean", "--output", str(tmp_path / "cli")]
    assert main(argv) == 0
    assert main(argv) == 2
