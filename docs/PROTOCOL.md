# Evaluation protocol: cheme-tabular-v1

## What is comparable

A benchmark identity hashes its complete task specification, including dataset digest, target/features/units, independent-unit definition, split configuration and frozen assignment digest, audit policy and accepted warnings, metric, model seeds, and scientific scope. A comparison accepts only one exact identity. Data curation changes, a different seed allocation, a new target, or a different feature list create a different identity and must receive a new benchmark version.

This release supports **scalar regression**. It does not claim to implement classification, time-series forecasting windows, surrogate-guided optimization regret, molecular graph neural-network training, or experimental design competitions. The process fixture tests response prediction, not the performance of an optimizer.

## Admission and official partitions

1. Validate the JSON specification, unique CSV columns and row IDs, numerical values, declared units, source and grouping metadata. Targets cannot be missing, identifiers cannot be model inputs, and official splits cannot condition on targets.
2. Verify exact dataset and frozen-partition SHA-256 digests. Regenerate partitions using pinned SciSplit and compare every original row ID/partition. Train, validation and test must all be nonempty; exclusions are forbidden.
3. Run ChemData Auditor on the official partitions with exact model features, target, provenance, numeric/unit checks, declared physical bounds and independent-unit grouping. Errors always block admission. Warnings require a task-card justification by finding code. All findings and evidence are preserved.
4. Independently check that no declared unit/group crosses partitions. Copy the unchanged dataset, specification, assignments, audit report and SciSplit diagnostics into a new prepared bundle with file hashes.

The installed upstream Python source is checked against the source digest for commit `eff3ed3c43ec71e9ceecabc1f04d1dfb5c91c116`. This is the explicit three-way SciSplit implementation pin, not a floating reference to the upstream default branch. If its code changes, preparation fails. A future upstream upgrade needs protocol review and new frozen assignments where necessary.

Group identities can be documented experimental units, explicitly limited proxies, or generated synthetic families. Multiple grouping columns have transitive semantics: sharing **any** identity joins observations into one group. Bootstrap and equal-group metrics use these same connected groups. Grouping is never evidence that a source actually contains independent replicates.

## Features and preprocessing

The specification lists numeric and categorical features explicitly. Source columns, row IDs, group IDs and unlisted metadata are excluded from model inputs. Only empty/whitespace numeric cells represent missing features; strings such as `NaN`, `Infinity`, malformed numbers and infinite values are rejected. Missing targets are never imputed.

Numerical features use training-median imputation, missingness indicators, and training-fitted standard scaling. A completely missing training column is kept by the imputer under the documented scikit-learn behavior; new missingness patterns do not create evaluation-fitted columns. Categorical features use a constant missing token and training-fitted one-hot encoding. Unseen evaluation categories map to all-zero known-category columns. Targets are not scaled or transformed.

These rules apply to every built-in baseline. External submissions must disclose their preprocessing and may claim protocol compliance only if they actually follow it; the scorer cannot inspect a submitted CSV's training history. All preprocessing and model fits occur on training rows, with validation reserved for selecting a fixed candidate and test reserved for evaluating that selected candidate. There is no train-plus-validation refit in v1.

## Baselines and selection

| Baseline | Fixed candidates | Notes |
| --- | --- | --- |
| `mean` | Training mean | No hyperparameter search |
| `ridge` | alpha = 0.1, 1, 10 | Same preprocessing as other models |
| `random_forest` | 100 trees; depth 8 or unlimited; minimum leaf size 2 | Fixed declared model seed; one job |
| `hist_gradient_boosting` | 100 iterations; 15 or 31 leaves; learning rate 0.1 | Early stopping disabled so no hidden internal validation split |

The lowest validation primary metric selects a candidate; ties use candidate-list order. Candidate validation scores and chosen parameters are saved. Test predictions occur after that selection. The default model seeds are 0, 1 and 2, distinct from the fixed split seed. Thread pools are limited to one for baseline execution. Software versions and a digest of the runner's Python source are recorded; bitwise reproducibility across hardware/library versions is not guaranteed.

## Metrics

Row MAE is the mean absolute error; RMSE is the square root of mean squared error. Equal-group MAE first averages absolute errors within each declared group, then averages those group errors equally. Equal-group RMSE averages within-group squared error, averages groups equally, then takes the square root. This prevents a group with a longer measurement series from dominating merely because it has more rows.

R² is reported only when the evaluation target has nonzero variance and at least two rows; otherwise it is `null`. Predictions must be finite and squared errors must not overflow. Targets and predictions retain the target unit; MAE and RMSE therefore retain physical units too.

The group-MAE interval is a 95% percentile bootstrap using 1000 resamples of whole declared groups and fixed bootstrap seed 0. With fewer than two groups it is `null`. It describes variation conditional on the fixed fitted model and held-out group set; it is not a confidence guarantee when grouping proxies misrepresent dependence. Few-group intervals can be unstable. Leaderboard seed standard deviation describes algorithm variation, not experimental uncertainty or split variation.

## Leaderboards and scientific claims

All submitted validation/test row IDs and partitions must match the official assignments exactly. Order can vary; missing, duplicated, extra or mislabeled predictions fail. The evaluator recomputes metrics and stores prediction hashes. Leaderboards revalidate the prepared benchmark, run identities, predictions and scores rather than trusting submitted metrics.

Ranks require every declared seed. Incomplete entries remain visible but unranked. Duplicate method/origin/code-reference/seed entries fail to discourage cherry-picking. Exact ties share a rank. Methods with different code references appear separately; models can use different implementations without changing the benchmark's feature/partition contract.

No global score averages incompatible physical targets, datasets, units or splits. Each task has its own leaderboard. Public labels and a local runner cannot prevent deliberate leakage, repeated test tuning, dishonest training declarations or selective reporting across method names. These are reproducible local comparisons, not a secure hosted competition or automatic evidence of scientific validity.
