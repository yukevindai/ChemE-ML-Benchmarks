# Concrete strength under composition holdout

**EMPIRICAL DATA — version 1.0.0**

Domain: materials. Task: predict `strength` (MPa). Rows: 1030.

## Source and curation

Yeh, I. (1998). Concrete Compressive Strength. UCI Machine Learning Repository. DOI: 10.24432/C5PK67.

Source: https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength

License: CC-BY-4.0. Retrieved: 2026-09-07.

Converted Concrete_Data.xls to UTF-8 CSV, renamed columns, retained all 1030 rows and numerical values, added source row IDs and SHA-256 recipe keys from the seven supplied ingredient quantities. No deduplication, imputation, target transformation, or unit conversion.

Data SHA-256: `797483250e397f6d45c43e2c975390c6204abb32276f8fa8e23bf73681b32b98`

## Independent unit

Experimental unit should be an independently prepared/cured specimen or batch; original batch/specimen IDs are absent. The operational grouping proxy is the exact seven-component recipe, shared across curing ages.

All observations with the same declared recipe stay together. This avoids testing the same recipe at another age, but does not establish independent experiments or resolve rounded near-identical recipes.

## Generalization

Prediction for held-out exact concrete compositions within this source collection, conditional on supplied age and ingredients.

Independent laboratory, publication, apparatus, chemistry-family or deployment transfer beyond the declared holdout.

## Features and units

| Variable | Role | Unit |
| --- | --- | --- |
| cement | numeric feature | kg/m^3 |
| slag | numeric feature | kg/m^3 |
| fly_ash | numeric feature | kg/m^3 |
| water | numeric feature | kg/m^3 |
| superplasticizer | numeric feature | kg/m^3 |
| coarse_aggregate | numeric feature | kg/m^3 |
| fine_aggregate | numeric feature | kg/m^3 |
| age | numeric feature | day |
| strength | target | MPa |

Identifiers and source metadata are excluded from model features.

## Evaluation

Official assignments are frozen in partitions.json and regenerated with pinned SciSplit for verification. Preprocessing fits on training rows only. Validation selects fixed-grid hyperparameters; test evaluates the selected model without refitting. Primary metric: equal-group MAE. Report all model seeds 0, 1, and 2.

## Limitations

- Batch, laboratory, study and specimen identities are unavailable; grouping is a conservative composition proxy, not documented experimental independence.
- Exact duplicate published records are retained; their experimental meaning is unknown. Equal-group metrics reduce between-recipe row-count weighting, but duplicates still affect within-recipe errors.
- Exact composition holdout does not ensure chemical distance, multivariate extrapolation, or transfer to new cement sources.

## Accepted Auditor warnings

- `duplicate_samples`: Retain published observations because replicate/duplicate identities are not documented; composition grouping prevents these exact repeated records crossing partitions.
