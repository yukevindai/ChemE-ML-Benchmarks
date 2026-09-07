# SYNTHETIC: catalyst conversion

**SYNTHETIC DATA — version 1.0.0**

Domain: catalysis. Task: predict `conversion` (dimensionless). Rows: 100.

## Source and curation

ChemE ML Benchmarks contributors (2026), deterministic synthetic software fixture.

Source: https://github.com/yukevindai/ChemE-ML-Benchmarks/blob/feat/benchmark-suite/scripts/curate.py

License: MIT. Retrieved: 2026-09-07.

Generated with NumPy seed 104; 20 mathematical families, five draws each. Explicit toy equation is in scripts/curate.py. No measurements or empirical uncertainty; class is a synthetic categorical nuisance feature.

Data SHA-256: `73153ee8f9ab8337478bb71fc0a510e7158125157586115de20583d6d27ff3ba`

## Independent unit

One generated mathematical parameter family (five related design points), not an experimental unit.

The family ID is held intact to test the grouping mechanism. The family parameter is a declared numerical input, not an inferred sample identifier.

## Generalization

Software behavior on held-out toy parameter values only; no real-world scientific performance claim.

Independent laboratory, publication, apparatus, chemistry-family or deployment transfer beyond the declared holdout.

## Features and units

| Variable | Role | Unit |
| --- | --- | --- |
| family_parameter | numeric feature | dimensionless |
| residence_time | numeric feature | s |
| temperature | numeric feature | K |
| class | categorical feature | category |
| conversion | target | dimensionless |

Identifiers and source metadata are excluded from model features.

## Evaluation

Official assignments are frozen in partitions.json and regenerated with pinned SciSplit for verification. Preprocessing fits on training rows only. Validation selects fixed-grid hyperparameters; test evaluates the selected model without refitting. Primary metric: equal-group MAE. Report all model seeds 0, 1, and 2.

## Limitations

- Synthetic fixture, not experimental data and not eligible for an empirical leaderboard.
- Toy equations omit mechanisms, measurement error, confounding, and realistic source heterogeneity.
- Good performance cannot establish validity for the named chemical-engineering application.

## Accepted Auditor warnings

- `target_proxy`: Toy analytical dependence may cause strong feature-target correlation; formula inputs are explicitly declared and available at prediction time.
