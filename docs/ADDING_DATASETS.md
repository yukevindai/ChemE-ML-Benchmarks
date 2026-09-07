# Admitting a real scientific dataset

Start with a new directory under `benchmarks/`, containing a UTF-8 CSV, `benchmark.json`, frozen `partitions.json`, and `CARD.md`. Use the existing empirical cards as complete schema examples; unknown JSON fields are rejected. Package installation does not modify these files.

Before declaring a benchmark, document:

- A retrievable primary source, appropriate redistribution license, citation, source-file hash, acquisition date, and exact transformations. Do not substitute a mirrored collection's license for the original data's license without verification.
- The prediction target, its units, features available at prediction time, task population and intended use. Outputs observed after the target measurement cannot silently become input features.
- What counts as an independent experiment: for example, a manufactured battery cell rather than a cycle, an adsorbent specimen rather than an isotherm point, a catalyst batch rather than an operating-condition sweep, or a process campaign rather than a timestamp.
- Available provenance keys and the limitations of any proxy grouping. If independent units are unknown, explicitly say so; never invent laboratory, publication, cell or run identities.
- What the official holdout tests and does not test: new compositions, scaffolds, laboratories, publications, time periods, clusters or extrapolation regions. All of these SciSplit designs are available through its explicit configuration, subject to complete nonempty three-way partitions.
- Physical/unit constraints, missingness rules and justified warning acceptance. Auditor errors cannot be waived. Curate excluded rows before freezing the benchmark and retain an exclusion ledger in the dataset card/source transformation record.

`scripts/curate.py` demonstrates deterministic curation and partition freezing for this release. It uses `partition_record` to generate a record containing the dataset digest, exact split configuration, pinned generator commit, and every row assignment. It then hashes that file into the task card and runs the same Auditor admission gate used for evaluation. Use `prepare` to verify a finished card; it cannot silently regenerate new official assignments.

To reproduce this release's empirical data, download the original UCI archives:

```bash
curl -L 'https://archive.ics.uci.edu/static/public/165/concrete+compressive+strength.zip' -o /tmp/concrete.zip
curl -L 'https://archive.ics.uci.edu/static/public/291/airfoil+self+noise.zip' -o /tmp/airfoil.zip
python scripts/curate.py --downloads /tmp --output outputs/recurated
```

Compare archive hashes against each checked-in specification's `source.raw_sha256`; changes require review. Recuration writes a new directory and refuses existing task directories. Do not overwrite a published benchmark under the same version when source data, units, identity grouping, audit policy or official partitions change.

The nine domain categories supported by the catalog are batteries, electrolytes, adsorption, catalysis, separations, thermodynamics, transport, materials and process optimization. Ten synthetic fixtures exercise them because batteries include separate retention and lifetime cases. Real-data expansion into the remaining domains is deliberately contingent on this admission process; toy calculations must never be relabeled as experimental observations.
