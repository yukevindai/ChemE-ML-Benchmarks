# ChemE ML Benchmarks

A local Python evaluation suite for chemically meaningful, reproducible machine-learning comparisons. Every task has a versioned dataset card, immutable data digest, independent-unit definition, frozen train/validation/test assignments, fixed preprocessing protocol, baseline search spaces, and documented limits on scientific interpretation.

**ChemData Auditor validates every prepared dataset. SciSplit generates and verifies its official partitions.** Baselines fit preprocessing on training rows only, choose hyperparameters on validation data, and evaluate the selected model on test data. Leaderboards recompute scores from predictions and refuse incompatible benchmark versions or partitions.

## Included benchmarks

| Task | Data | Scientific holdout | Scope |
| --- | --- | --- | --- |
| [Concrete strength](benchmarks/concrete-strength/CARD.md) | 1,030 UCI observations, CC BY 4.0 | Exact seven-component composition holdout; recipe groups shared across curing ages | Held-out recipes within the source collection; batch/lab identities are missing |
| [Airfoil self-noise](benchmarks/airfoil-noise/CARD.md) | 1,503 UCI observations, CC BY 4.0 | Chord-length extrapolation with whole condition groups | Larger chord lengths within the supplied NACA 0012 collection; not arbitrary airfoils |
| [Ten synthetic fixtures](docs/CATALOG.md) | Deterministic toy calculations | Whole generated parameter-family holdout | Software validation only, covering batteries, electrolytes, adsorption, catalysis, separations, thermodynamics, transport, materials and process-response prediction |

The empirical datasets are curated and auditable, but their independent experimental units are only partially documented. Their grouping proxies and limitations are explicit. Synthetic fixtures are labeled in cards, machine-readable specifications, and leaderboards; they are not empirical benchmark evidence. Additional real datasets in the other domains require source, licensing, provenance, and independence review before admission.

## Install and run

```bash
python -m pip install -e '.[dev]'
python -m cheme_benchmarks list
python -m cheme_benchmarks prepare benchmarks/concrete-strength/benchmark.json --output outputs/concrete
python -m cheme_benchmarks run outputs/concrete --model ridge --seed 0 --output outputs/ridge-0
```

The `cheme-bench` command is equivalent to `python -m cheme_benchmarks`. Use new output paths; existing results are never overwritten. The package pins ChemData Auditor/SciSplit to commit `eff3ed3c43ec71e9ceecabc1f04d1dfb5c91c116`, which contains the three-way SciSplit API, and verifies its Python source digest before making official partitions. Installation requires Git/network access; evaluation uses the checked-in data and runs locally without downloads.

Run the complete empirical suite and create separate leaderboards:

```bash
cheme-bench suite --kind empirical --models mean ridge random_forest --output outputs/empirical
cheme-bench suite --kind synthetic --models mean --output outputs/smoke
python -m pytest -q
```

Each suite run includes all three declared model seeds. Failed tasks remain explicit in `suite.json`; there is no fallback split or silent row exclusion. Regression baselines include a training-mean predictor, ridge regression, random forest, and histogram gradient boosting. Reference results and prediction files are in [results/reference](results/reference).

## Compare another method

Export a CSV with exactly `row_id,partition,prediction`, covering every official validation and test row, and provide method metadata. Then:

```bash
cheme-bench submit outputs/concrete --predictions predictions.csv --method method.json --output outputs/submission
cheme-bench leaderboard outputs/concrete outputs/ridge-0 outputs/ridge-1 outputs/ridge-2 --output outputs/leaderboard
```

Only complete declared seed sets receive ranks. The default primary score is equal-group MAE; row-weighted MAE/RMSE, group RMSE, R² and group-bootstrap intervals are retained. Never average physical errors across unrelated targets or units. Local scoring verifies predictions, not whether an external method secretly used public test labels.

See the [evaluation protocol](docs/PROTOCOL.md), [submission format](docs/SUBMISSIONS.md), [dataset admission guide](docs/ADDING_DATASETS.md), and [data licenses](DATA_LICENSES.md).
