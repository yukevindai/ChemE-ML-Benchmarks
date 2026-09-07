# Validation and reproducibility

The test suite exercises every included task's Auditor admission and frozen SciSplit assignment verification. It also checks:

- Explicit train/validation/test coverage and independent-unit isolation.
- Dataset/partition tampering, invalid feature/target declarations, reserved identity roles, and target-conditioned split rejection.
- Auditor errors that cannot be waived and newly introduced warnings that require documented acceptance.
- Training-only imputation/scaling and handling of unseen evaluation categories.
- Row versus equal-group metric arithmetic, constant-target R², group-level bootstrap intervals, transitive identity grouping and non-finite/overflowing predictions.
- All four baseline families; exact official prediction IDs; reordered predictions; missing, repeated and mislabeled submissions.
- Recomputed score integrity, external method declarations, complete seed sets, duplicate submissions, and CLI output protection.

Run `python -m pytest -q`. CI installs the pinned upstream dependency and runs the suite on Python 3.10 and 3.12. Development tests use actual ChemData Auditor and SciSplit, not substitute implementations.

The end-to-end `suite` command was also run for the two empirical tasks with three baseline families and all three model seeds. Reference prediction bundles are checked in. The synthetic suite is a separate execution path for all ten fixtures and does not create empirical performance claims.

Tests establish software and contract invariants. They do not validate source authorship, experimental independence, honesty of external training, causal interpretations, complete literature coverage or universal performance claims.
