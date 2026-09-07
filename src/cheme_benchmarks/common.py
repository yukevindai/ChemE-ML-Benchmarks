"""Deterministic identities and strict artifact IO."""
import csv
import hashlib
import io
import json
import math
import shutil
import tempfile
from contextlib import contextmanager
from importlib.metadata import version
from pathlib import Path

AUDITOR_COMMIT = "eff3ed3c43ec71e9ceecabc1f04d1dfb5c91c116"
AUDITOR_SOURCE_SHA256 = "4fd117f76555526eac5cb52344f4e4814bce415079555d7a50a2f889a79ab58a"
PROTOCOL = "cheme-tabular-v1"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def read_json(path):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError(f"Duplicate JSON key: {k}")
            result[k] = v
        return result
    def invalid(v):
        raise ValueError(f"Non-finite JSON token: {v}")
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=invalid)


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def fields(obj, required, optional=()):
    if not isinstance(obj, dict) or set(required) - set(obj) or set(obj) - set(required) - set(optional):
        raise ValueError(f"Expected required keys {sorted(required)}, optional {sorted(optional)}")


def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def names(value, name, empty=False):
    if not isinstance(value, list) or (not empty and not value) or any(not isinstance(v, str) or not v.strip() for v in value) or len(set(value)) != len(value):
        raise ValueError(f"{name} must be a list of unique nonempty names")
    return value


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def safe_path(root, relative):
    root = Path(root).resolve()
    text(relative, "path")
    result = (root / relative).resolve()
    if Path(relative).is_absolute() or not result.is_relative_to(root):
        raise ValueError("Artifact path escapes its bundle")
    return result


def csv_frame(raw):
    import pandas as pd
    reader = csv.reader(io.StringIO(raw.decode("utf-8"), newline=""), strict=True)
    rows = list(reader)
    if len(rows) < 2 or not rows[0] or len(set(rows[0])) != len(rows[0]) or any(not c.strip() for c in rows[0]):
        raise ValueError("CSV requires unique named columns and data rows")
    if any(len(r) != len(rows[0]) for r in rows[1:]):
        raise ValueError("Ragged CSV records")
    return pd.DataFrame(rows[1:], columns=rows[0])


def csv_bytes(frame):
    return frame.to_csv(index=False, lineterminator="\n", float_format="%.17g").encode("utf-8")


def software():
    return {p: version(p) for p in ("cheme-ml-benchmarks", "chemdata-auditor", "numpy", "pandas", "scikit-learn", "pint")}


def source_digest(root):
    root = Path(root)
    h = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        h.update(path.relative_to(root).as_posix().encode())
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


@contextmanager
def new_directory(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Output already exists: {path}")
    temp = Path(tempfile.mkdtemp(prefix=".cheme-", dir=path.parent))
    try:
        yield temp
        path.mkdir()
        try:
            for child in temp.iterdir():
                child.rename(path / child.name)
        except BaseException:
            shutil.rmtree(path)
            raise
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def manifest_files(root):
    return {str(p.relative_to(root)): digest(p.read_bytes()) for p in sorted(Path(root).rglob("*")) if p.is_file()}


def verify_files(root, manifest):
    for path, expected in manifest["files"].items():
        if digest(safe_path(root, path).read_bytes()) != expected:
            raise ValueError(f"Artifact hash mismatch: {path}")
