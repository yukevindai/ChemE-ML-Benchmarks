import shutil
from pathlib import Path

import pytest

from cheme_benchmarks import prepare

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def task(tmp_path):
    root = tmp_path / "task"
    shutil.copytree(ROOT / "benchmarks" / "synthetic-adsorption-isotherm", root)
    return root


@pytest.fixture
def prepared(task, tmp_path):
    out = tmp_path / "prepared"
    prepare(task / "benchmark.json", out)
    return out
