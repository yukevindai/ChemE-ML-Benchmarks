# External predictions and reproducible results

Create predictions for every validation and test row in `prepared/partitions.json`:

```csv
row_id,partition,prediction
uci165-0001,test,38.2
uci165-0002,validation,41.1
```

The rows above illustrate the format only; use the actual official assignments. Include neither training rows nor extra IDs. Predict the original target in its declared units. There is no implicit inverse transform or imputation by the scorer.

Provide `method.json`:

```json
{
  "name": "my-regressor",
  "seed": 0,
  "origin": "external",
  "code_reference": "https://github.com/OWNER/REPO/commit/FULL_COMMIT_SHA",
  "training_description": "Explain training-only preprocessing, feature availability, validation selection and any departure from the benchmark protocol.",
  "parameters": {"example_parameter": 10},
  "validation_search": [
    {"parameters": {"example_parameter": 10}, "validation_primary": 4.2}
  ]
}
```

Use real code references and truthful training descriptions. External training metadata is a declaration, not verified provenance. `origin: builtin` is reserved for the runner and rejected by the external submission command. Save separate results for each declared seed; a complete method needs seeds 0, 1 and 2 for included tasks.

```bash
cheme-bench submit outputs/concrete --predictions predictions.csv --method method.json --output outputs/my-method-0
cheme-bench leaderboard outputs/concrete outputs/my-method-0 outputs/my-method-1 outputs/my-method-2 --output outputs/my-leaderboard
```

A run bundle contains `predictions.csv`, `run.json`, and a manifest with file hashes. `run.json` includes benchmark identity, method metadata, selected parameters, validation/test metrics, software versions, and a content-derived run ID. A leaderboard recomputes scores from the original targets and prediction files before aggregation. Editing scores and updating a file digest cannot change the recomputed result.

To compare checked-in reference predictions, prepare the matching task and pass the corresponding `results/reference/TASK/runs/MODEL-SEED` directories to `leaderboard`. A changed task specification or official partition will be rejected even if its display name is unchanged.
