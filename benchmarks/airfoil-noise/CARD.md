# Airfoil noise under chord-length extrapolation

**EMPIRICAL DATA — version 1.0.0**

Domain: transport. Task: predict `sound_pressure` (dB). Rows: 1503.

## Source and curation

Brooks, T., Pope, D., and Marcolini, M. (1989). Airfoil Self-Noise. UCI Machine Learning Repository. DOI: 10.24432/C5VW2C.

Source: https://archive.ics.uci.edu/dataset/291/airfoil+self+noise

License: CC-BY-4.0. Retrieved: 2026-09-07.

Converted the whitespace-delimited source file to CSV, renamed columns, retained all 1503 rows and numerical values, added row IDs and condition keys from angle/chord/velocity/displacement thickness. No feature/target scaling, row deletion, or unit conversion.

Data SHA-256: `225e358625eb4c9a2e48d20506871342230ecaa5ba827cbe9f26da51d79a8344`

## Independent unit

Experimental unit should be an independently acquired wind-tunnel condition/run, not each frequency-bin measurement. Run IDs are absent; supplied angle/chord/velocity/displacement-thickness tuples form the operational condition proxy.

All frequency observations sharing a condition stay together. Chord extrapolation also keeps an entire nominal chord level in one partition.

## Generalization

Prediction at chord lengths >0.2286 m, with validation at (0.1524,0.2286] m and training <=0.1524 m, within the supplied NACA 0012 collection.

Independent laboratory, publication, apparatus, chemistry-family or deployment transfer beyond the declared holdout.

## Features and units

| Variable | Role | Unit |
| --- | --- | --- |
| frequency | numeric feature | Hz |
| angle | numeric feature | degree |
| chord | numeric feature | m |
| velocity | numeric feature | m/s |
| displacement_thickness | numeric feature | m |
| sound_pressure | target | dB |

Identifiers and source metadata are excluded from model features.

## Evaluation

Official assignments are frozen in partitions.json and regenerated with pinned SciSplit for verification. Preprocessing fits on training rows only. Validation selects fixed-grid hyperparameters; test evaluates the selected model without refitting. Primary metric: equal-group MAE. Report all model seeds 0, 1, and 2.

## Limitations

- No documented run, specimen, laboratory or publication IDs; condition groups cannot certify independent experimental replicates.
- NACA 0012 geometry family, source apparatus, span and observer settings limit transfer; this does not test arbitrary airfoils or transport laws.
- Target is the source's scaled sound-pressure value in dB, not an unscaled acoustic pressure or sound-power estimate.
