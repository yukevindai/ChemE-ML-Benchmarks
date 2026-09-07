# Reproducible empirical reference results

These are actual local executions of the checked-in v1.0.0 task specifications, using the v0.1.0 runner and model seeds 0, 1 and 2. Each task includes mean, ridge and random-forest runs, selected using validation data. Histogram gradient boosting is also implemented and tested but is not included in this reference snapshot.

| Task | Baseline | Mean test group-MAE | Target unit |
| --- | --- | --- | --- |
| Concrete composition holdout | Mean | 11.7720 | MPa |
| Concrete composition holdout | Ridge | 7.4099 | MPa |
| Concrete composition holdout | Random forest | 4.6737 | MPa |
| Airfoil chord extrapolation | Mean | 5.3960 | dB |
| Airfoil chord extrapolation | Ridge | 3.6688 | dB |
| Airfoil chord extrapolation | Random forest | 2.5246 | dB |

Values above are rounded summaries. Exact per-seed predictions, validation searches, selected parameters, metrics, software versions, runner source digests and run identities are retained under each task's `runs/`. JSON/Markdown/HTML leaderboards are under `leaderboard/`.

Recompute a reference leaderboard from its prediction files:

```bash
python -m cheme_benchmarks prepare benchmarks/concrete-strength/benchmark.json --output outputs/reference-check
python -m cheme_benchmarks leaderboard outputs/reference-check results/reference/concrete-strength/runs/* --output outputs/reference-board
```

Re-execute the models:

```bash
python -m cheme_benchmarks suite --kind empirical --models mean ridge random_forest --output outputs/reference-rerun
```

The source-code digest identifies exactly which runner files produced these results. Library/hardware differences can change floating-point calculations or stochastic model outcomes; versions are recorded rather than silently treated as identical. The official dataset/partition and preprocessing contract remains fixed.

These results do not establish general superiority across chemistry, experimental independence of undocumented source units, or out-of-source deployment accuracy. The two tasks have different units and scientific questions, so their numbers must not be pooled into a global ranking. Synthetic smoke-test runs are intentionally not presented as empirical results here.
