"""Recompute every score and compare only one exact scientific protocol at a time."""
import html
from collections import defaultdict

import numpy as np

from .common import new_directory, write_json
from .evaluate import load_run
from .prepare import load_prepared


def leaderboard(prepared, run_directories, destination=None):
    spec, _, _, manifest = load_prepared(prepared)
    if not run_directories:
        raise ValueError("Leaderboard requires evaluated runs")
    collected = defaultdict(list)
    seen = set()
    for directory in run_directories:
        record = load_run(prepared, directory)
        method = record["method"]
        key = (method["name"], method["origin"], method["code_reference"])
        identity = (*key, method["seed"])
        if identity in seen:
            raise ValueError("Duplicate method/seed submission; do not cherry-pick repeated runs")
        if type(method["seed"]) is not int or method["seed"] not in spec["model_seeds"]:
            raise ValueError("Run seed is outside the official protocol")
        seen.add(identity)
        collected[key].append(record)
    entries = []
    for key, runs in collected.items():
        runs.sort(key=lambda r: r["method"]["seed"])
        complete = {r["method"]["seed"] for r in runs} == set(spec["model_seeds"])
        primary = spec["primary_metric"]
        scores = [r["metrics"]["test"][primary] for r in runs]
        entries.append({"method": key[0], "origin": key[1], "code_reference": key[2], "complete": complete,
                        "seeds": [r["method"]["seed"] for r in runs], "test_primary_mean": float(np.mean(scores)),
                        "test_primary_seed_std": float(np.std(scores, ddof=1)) if len(scores) > 1 else None,
                        "validation_primary_mean": float(np.mean([r["metrics"]["validation"][primary] for r in runs])),
                        "runs": [r["run_id"] for r in runs], "per_seed_metrics": [r["metrics"] for r in runs],
                        "rank": None})
    entries.sort(key=lambda e: (not e["complete"], e["test_primary_mean"], e["method"], e["code_reference"]))
    for i, entry in enumerate(entries):
        if entry["complete"]:
            # Competition ranks preserve exact ties.
            entry["rank"] = 1 + sum(other["complete"] and other["test_primary_mean"] < entry["test_primary_mean"] for other in entries)
    report = {"schema_version": "1.0", "benchmark_id": manifest["benchmark_id"], "benchmark": spec["id"],
              "version": spec["version"], "data_kind": spec["data_kind"], "primary_metric": spec["primary_metric"],
              "target_unit": spec["units"][spec["target"]], "direction": "lower_is_better", "required_seeds": spec["model_seeds"],
              "entries": entries, "generalization": spec["generalization"], "independence": spec["independence"],
              "limitations": spec["limitations"] + ["Seed standard deviation measures algorithm variation, not experimental uncertainty.",
                "This local public-data leaderboard validates scores, not honest training or absence of test-set tuning.",
                "Ranks compare this exact task only; metrics from different targets, units, or splits must not be pooled."]}
    if destination is not None:
        with new_directory(destination) as out:
            write_json(out / "leaderboard.json", report)
            lines = [f"# {spec['title']}", "", f"Data: {spec['data_kind']}. Metric: {spec['primary_metric']} ({report['target_unit']}); lower is better.", "",
                     "| Rank | Method | Seeds | Test mean | Seed SD |", "| --- | --- | --- | --- | --- |"]
            for e in entries:
                label = html.escape(e["method"]).replace("|", "\\|").replace("\n", " ").replace("\r", " ")
                lines.append(f"| {e['rank'] or 'incomplete'} | {label} | {e['seeds']} | {e['test_primary_mean']:.6g} | {e['test_primary_seed_std']} |")
            lines += ["", "Generalization: " + spec["generalization"]["supports"], "", "Limitations:", ""]
            lines += ["- " + limitation for limitation in report["limitations"]]
            md = "\n".join(lines) + "\n"
            (out / "leaderboard.md").write_bytes(md.encode())
            (out / "leaderboard.html").write_bytes(('<!doctype html><html lang="en"><meta charset="utf-8"><title>ChemE benchmark leaderboard</title><style>body{max-width:1100px;margin:3rem auto;padding:1rem;font:16px system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><body><pre>' + html.escape(md) + '</pre></body></html>').encode())
    return report
