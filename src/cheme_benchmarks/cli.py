"""Unified local benchmark commands."""
import argparse
import json
import sys
from pathlib import Path

from .common import read_json, write_json
from .evaluate import run_baseline, submit
from .leaderboard import leaderboard
from .models import GRIDS
from .prepare import prepare


def main(argv=None):
    p = argparse.ArgumentParser(prog="cheme-bench")
    sub = p.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list")
    listing.add_argument("--catalog", default="benchmarks")
    prep = sub.add_parser("prepare")
    prep.add_argument("spec")
    prep.add_argument("--output", required=True)
    run = sub.add_parser("run")
    run.add_argument("prepared")
    run.add_argument("--model", choices=list(GRIDS), required=True)
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--output", required=True)
    score = sub.add_parser("submit")
    score.add_argument("prepared")
    score.add_argument("--predictions", required=True)
    score.add_argument("--method", required=True)
    score.add_argument("--output", required=True)
    board = sub.add_parser("leaderboard")
    board.add_argument("prepared")
    board.add_argument("runs", nargs="+")
    board.add_argument("--output", required=True)
    suite = sub.add_parser("suite")
    suite.add_argument("--catalog", default="benchmarks")
    suite.add_argument("--models", nargs="+", choices=list(GRIDS), default=["mean", "ridge"])
    suite.add_argument("--kind", choices=["empirical", "synthetic", "all"], default="empirical")
    suite.add_argument("--output", required=True)
    args = p.parse_args(argv)
    try:
        code = 0
        if args.command == "list":
            result = [{k: read_json(path)[k] for k in ("id", "title", "domain", "data_kind", "version")} for path in sorted(Path(args.catalog).glob("*/benchmark.json"))]
        elif args.command == "prepare":
            result = prepare(args.spec, args.output)
        elif args.command == "run":
            result = run_baseline(args.prepared, args.model, args.output, args.seed)
        elif args.command == "submit":
            result = submit(args.prepared, args.predictions, args.method, args.output)
        elif args.command == "leaderboard":
            result = leaderboard(args.prepared, args.runs, args.output)
        else:
            paths = [path for path in sorted(Path(args.catalog).glob("*/benchmark.json")) if args.kind == "all" or read_json(path)["data_kind"] == args.kind]
            if not paths:
                raise ValueError("No benchmarks match the requested catalog/kind")
            destination = Path(args.output)
            destination.mkdir(parents=True, exist_ok=False)
            result = []
            for path in paths:
                spec = read_json(path)
                root = destination / spec["id"]
                try:
                    prepare(path, root / "prepared")
                    runs = []
                    for model in dict.fromkeys(args.models):
                        for seed in spec["model_seeds"]:
                            out = root / "runs" / f"{model}-{seed}"
                            run_baseline(root / "prepared", model, out, seed)
                            runs.append(out)
                    leaderboard(root / "prepared", runs, root / "leaderboard")
                    result.append({"benchmark": spec["id"], "status": "ok", "runs": len(runs)})
                except (ValueError, OSError, KeyError, TypeError) as exc:
                    code = 1
                    result.append({"benchmark": spec["id"], "status": "failed", "error": str(exc)})
            write_json(destination / "suite.json", result)
        print(json.dumps(result, indent=2, allow_nan=False))
        return code
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"cheme-bench: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
