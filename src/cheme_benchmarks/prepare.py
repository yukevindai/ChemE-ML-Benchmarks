"""Auditor admission gate and frozen SciSplit partitions."""
from pathlib import Path

from chemdata_auditor import AuditConfig, SplitConfig, audit, split

from .common import (AUDITOR_COMMIT, AUDITOR_SOURCE_SHA256, PROTOCOL, canonical, digest, manifest_files,
                     new_directory, read_json, software, source_digest, verify_files, write_json)
from .spec import load_benchmark, load_data, validate_spec


def partition_record(spec, frame):
    import chemdata_auditor
    if source_digest(Path(chemdata_auditor.__file__).parent) != AUDITOR_SOURCE_SHA256:
        raise ValueError("Installed ChemData Auditor/SciSplit source differs from the pinned official implementation")
    result = split(frame, SplitConfig(**spec["split"]))
    if not result.train or not result.validation or not result.test:
        raise ValueError("Official benchmarks require nonempty train, validation and test partitions")
    if result.excluded:
        raise ValueError("Official benchmark data must be curated before splitting; excluded rows are not permitted")
    return {"schema_version": "1.0", "dataset_sha256": spec["data"]["sha256"],
            "split_config": spec["split"], "generator": {"name": "SciSplit", "commit": AUDITOR_COMMIT},
            "assignments": [{"row_id": str(r), "partition": p} for r, p in zip(frame[spec["data"]["row_id"]], result.assignments())]}, result


def inspect(spec, frame, frozen):
    generated, split_result = partition_record(spec, frame)
    if generated != frozen:
        raise ValueError("SciSplit output differs from frozen official partitions; publish a new benchmark version")
    checked = frame.copy()
    checked["_official_partition"] = split_result.assignments()
    cfg = dict(spec["audit"])
    cfg["split_column"] = "_official_partition"
    cfg["group_columns"] = list(dict.fromkeys([*spec["independence"]["columns"], *cfg.get("group_columns", [])]))
    cfg["numeric_columns"] = list(dict.fromkeys([*spec["features"]["numeric"], spec["target"], *cfg.get("numeric_columns", [])]))
    cfg["units"] = {}
    for i, (col, unit) in enumerate(spec["units"].items()):
        unit_col = f"_benchmark_unit_{i}"
        if unit_col in checked:
            raise ValueError("Dataset uses reserved unit metadata column")
        checked[unit_col] = unit
        cfg["units"][col] = {"column": unit_col, "expected": unit}
    report = audit(checked, AuditConfig(**cfg))
    blocked = [f for f in report.findings if f.severity == "error" or (f.severity == "warning" and f.code not in spec["accepted_warnings"])]
    if blocked:
        raise ValueError("Auditor admission failed: " + ", ".join(sorted({f.code for f in blocked})))
    # Additional explicit invariant independent of Auditor finding-code conventions.
    labels = checked["_official_partition"]
    for col in spec["independence"]["columns"]:
        if checked.groupby(col, dropna=False)["_official_partition"].nunique().max() != 1:
            raise ValueError("Independent experimental unit crosses official partitions")
    if "_official_partition" in frame:
        raise ValueError("Dataset uses reserved partition column")
    return report.to_dict(), split_result.to_dict()


def benchmark_identity(spec):
    return "benchmark_" + digest(canonical({"spec": spec, "protocol": PROTOCOL, "auditor_commit": AUDITOR_COMMIT}))


def prepare(spec_path, destination):
    spec, frame, raw, frozen, frozen_raw = load_benchmark(spec_path)
    audit_report, split_report = inspect(spec, frame, frozen)
    benchmark_id = benchmark_identity(spec)
    with new_directory(destination) as out:
        write_json(out / "spec.json", spec)
        (out / "dataset.csv").write_bytes(raw)
        (out / "partitions.json").write_bytes(frozen_raw)
        write_json(out / "audit.json", audit_report)
        write_json(out / "scisplit.json", split_report)
        write_json(out / "manifest.json", {"schema_version": "1.0", "benchmark_id": benchmark_id,
                    "files": manifest_files(out), "software": software(), "auditor_commit": AUDITOR_COMMIT,
                    "admission": "passed_with_documented_warnings" if any(f["severity"] == "warning" for f in audit_report["findings"]) else "passed"})
    return {"benchmark_id": benchmark_id, "rows": len(frame), "sizes": {p: sum(a["partition"] == p for a in frozen["assignments"]) for p in ("train", "validation", "test")}}


def load_prepared(directory):
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    if set(manifest["files"]) != {"spec.json", "dataset.csv", "partitions.json", "audit.json", "scisplit.json"}:
        raise ValueError("Prepared manifest must cover exactly the protocol artifacts")
    verify_files(directory, manifest)
    spec = validate_spec(read_json(directory / "spec.json"))
    if benchmark_identity(spec) != manifest["benchmark_id"] or manifest["auditor_commit"] != AUDITOR_COMMIT:
        raise ValueError("Benchmark identity or upstream pin mismatch")
    raw = (directory / "dataset.csv").read_bytes()
    frame = load_data(spec, raw)
    frozen_raw = (directory / "partitions.json").read_bytes()
    if digest(frozen_raw) != spec["partitions"]["sha256"]:
        raise ValueError("Prepared partitions differ from task card")
    frozen = read_json(directory / "partitions.json")
    audit_report, split_report = inspect(spec, frame, frozen)
    # Software metadata can differ on another machine; evidence and assignments cannot.
    retained_audit = read_json(directory / "audit.json")
    if {k: v for k, v in retained_audit.items() if k != "metadata"} != {k: v for k, v in audit_report.items() if k != "metadata"}:
        raise ValueError("Prepared audit differs from current source validation")
    retained_split = read_json(directory / "scisplit.json")
    if {k: v for k, v in retained_split.items() if k != "metadata"} != {k: v for k, v in split_report.items() if k != "metadata"}:
        raise ValueError("Prepared SciSplit report differs from official assignments or diagnostics")
    return spec, frame, frozen, manifest
