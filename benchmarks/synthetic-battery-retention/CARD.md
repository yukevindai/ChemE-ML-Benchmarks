# SYNTHETIC: battery retention

**SYNTHETIC DATA — version 1.0.0**

Domain: batteries. Task: predict `retention` (dimensionless). Rows: 100.

## Source and curation

ChemE ML Benchmarks contributors (2026), deterministic synthetic software fixture.

Source: https://github.com/yukevindai/ChemE-ML-Benchmarks/blob/feat/benchmark-suite/scripts/curate.py

License: MIT. Retrieved: 2026-09-07.

Generated with NumPy seed 100; 20 mathematical families, five draws each. Explicit toy equation is in scripts/curate.py. No measurements or empirical uncertainty; class is a synthetic categorical nuisance feature.

Data SHA-256: `5a287c189d824cb23bafb5c3e11a8d477005f0dac13c3cc0d487a82cdab9ce7b`

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
| cycle | numeric feature | dimensionless |
| rate | numeric feature | dimensionless |
| class | categorical feature | category |
| retention | target | dimensionless |

Identifiers and source metadata are excluded from model features.

## Evaluation

Official assignments are frozen in partitions.json and regenerated with pinned SciSplit for verification. Preprocessing fits on training rows only. Validation selects fixed-grid hyperparameters; test evaluates the selected model without refitting. Primary metric: equal-group MAE. Report all model seeds 0, 1, and 2.

## Limitations

- Synthetic fixture, not experimental data and not eligible for an empirical leaderboard.
- Toy equations omit mechanisms, measurement error, confounding, and realistic source heterogeneity.
- Good performance cannot establish validity for the named chemical-engineering application.

## Accepted Auditor warnings

- `target_proxy`: Toy analytical dependence may cause strong feature-target correlation; formula inputs are explicitly declared and available at prediction time.
