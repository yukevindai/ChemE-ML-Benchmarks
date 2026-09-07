import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cheme_benchmarks import prepare, load_prepared
from cheme_benchmarks.common import digest, read_json
from cheme_benchmarks.evaluate import group_ids
from cheme_benchmarks.metrics import regression_metrics
from cheme_benchmarks.models import preprocessing
from cheme_benchmarks.spec import validate_spec

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("task", sorted((ROOT / "benchmarks").glob("*/benchmark.json")))
def test_every_curated_and_synthetic_task_passes_auditor_and_scisplit(task, tmp_path):
    summary = prepare(task, tmp_path / "prepared")
    assert sum(summary["sizes"].values()) == summary["rows"]
    spec, frame, frozen, _ = load_prepared(tmp_path / "prepared")
    labels = [row["partition"] for row in frozen["assignments"]]
    for group in spec["independence"]["columns"]:
        assert frame.assign(partition=labels).groupby(group).partition.nunique().max() == 1


def test_frozen_partition_change_is_rejected(task, tmp_path):
    frozen = read_json(task / "partitions.json")
    frozen["assignments"][0]["partition"] = "test" if frozen["assignments"][0]["partition"] != "test" else "train"
    (task / "partitions.json").write_text(json.dumps(frozen))
    spec = read_json(task / "benchmark.json")
    spec["partitions"]["sha256"] = digest((task / "partitions.json").read_bytes())
    (task / "benchmark.json").write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="frozen"):
        prepare(task / "benchmark.json", tmp_path / "bad")


def test_changed_data_and_prepared_report_are_rejected(task, prepared, tmp_path):
    (task / "data.csv").write_bytes((task / "data.csv").read_bytes() + b"extra")
    with pytest.raises(ValueError, match="digest"):
        prepare(task / "benchmark.json", tmp_path / "bad")
    (prepared / "audit.json").write_text("{}")
    with pytest.raises(ValueError, match="hash"):
        load_prepared(prepared)


@pytest.mark.parametrize("change", ["target_feature", "identifier_feature", "drop_group", "target_split", "unknown_field"])
def test_invalid_scientific_contracts(task, change):
    spec = read_json(task / "benchmark.json")
    if change == "target_feature":
        spec["features"]["numeric"].append(spec["target"])
    elif change == "identifier_feature":
        spec["features"]["categorical"].append("group_id")
    elif change == "drop_group":
        spec["split"]["group_columns"] = []
    elif change == "target_split":
        spec["split"]["columns"] = [spec["target"]]
    else:
        spec["mispelled"] = True
    with pytest.raises(ValueError):
        validate_spec(spec)


def test_preprocessing_does_not_learn_from_validation_or_test():
    train = pd.DataFrame({"x": [1.0, np.nan, 3.0], "category": ["A", "A", "B"]})
    evaluation = pd.DataFrame({"x": [1000000.0, np.nan], "category": ["NEVER_SEEN", "A"]})
    transformer = preprocessing({"numeric": ["x"], "categorical": ["category"]})
    transformer.fit(train)
    stats = transformer.named_transformers_["numeric"].named_steps["impute"].statistics_.copy()
    mean = transformer.named_transformers_["numeric"].named_steps["scale"].mean_.copy()
    result = transformer.transform(evaluation)
    assert stats.tolist() == [2.0]
    assert mean[0] == 2.0
    assert np.isfinite(result).all()
    assert transformer.named_transformers_["numeric"].named_steps["impute"].statistics_.tolist() == [2.0]
    assert "NEVER_SEEN" not in transformer.named_transformers_["categorical"].named_steps["encode"].categories_[0]


def test_group_metrics_weight_units_and_keep_constant_target_r2_undefined():
    metric = regression_metrics([0, 0, 0, 0], [1, 1, 1, 9], ["a", "a", "a", "b"])
    assert metric["mae"] == 3
    assert metric["group_mae"] == 5
    assert metric["group_rmse"] == pytest.approx(np.sqrt(41))
    assert metric["r2"] is None
    assert metric["group_mae_interval95"] == [1, 9]
    assert regression_metrics([0], [1], ["one"])["group_mae_interval95"] is None


def test_transitive_identity_groups_are_one_metric_unit():
    frame = pd.DataFrame({"cell": ["a", "a", "b", "c"], "batch": ["x", "y", "y", "z"]})
    groups = group_ids(frame, ["cell", "batch"])
    assert groups[0] == groups[1] == groups[2]
    assert groups[2] != groups[3]


def test_nonfinite_and_overflowing_predictions_rejected():
    for value in (float("nan"), float("inf"), 1e300):
        with pytest.raises(ValueError):
            regression_metrics([0.0], [value], ["a"])
