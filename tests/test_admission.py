import json

import pytest

from cheme_benchmarks import prepare
from cheme_benchmarks.common import read_json


def test_error_cannot_be_waived(task, tmp_path):
    spec = read_json(task / "benchmark.json")
    spec["audit"]["bounds"] = {spec["target"]: [0, 0]}
    spec["accepted_warnings"]["out_of_bounds"] = "This must not override an error"
    (task / "benchmark.json").write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="out_of_bounds"):
        prepare(task / "benchmark.json", tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


def test_new_warning_requires_documented_acceptance(task, tmp_path):
    spec = read_json(task / "benchmark.json")
    spec["audit"]["correlation_threshold"] = 0.01
    spec["accepted_warnings"] = {}
    (task / "benchmark.json").write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="target_proxy"):
        prepare(task / "benchmark.json", tmp_path / "bad")
