# Data licenses and attribution

The repository code and original synthetic fixtures are MIT licensed under `LICENSE`. The MIT license does **not** replace the licenses of third-party datasets.

## Concrete Compressive Strength

Yeh, I. (1998). Concrete Compressive Strength [Dataset]. UCI Machine Learning Repository. DOI: [10.24432/C5PK67](https://doi.org/10.24432/C5PK67).

Source and license declaration: [UCI dataset 165](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength). Distributed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

Adaptations: Excel-to-CSV conversion, renamed column headers, source row IDs, exact ingredient-recipe grouping IDs, task cards, and benchmark partitions. All original rows are retained. Values are serialized at floating-point precision; no intentional measurement corrections, unit conversion, deduplication, or target transformation is performed. Attribution does not imply endorsement by the source authors.

## Airfoil Self-Noise

Brooks, T., Pope, D., and Marcolini, M. (1989). Airfoil Self-Noise [Dataset]. UCI Machine Learning Repository. DOI: [10.24432/C5VW2C](https://doi.org/10.24432/C5VW2C).

Source and license declaration: [UCI dataset 291](https://archive.ics.uci.edu/dataset/291/airfoil+self+noise). Distributed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

Adaptations: whitespace-delimited-to-CSV conversion, renamed headers, source row IDs, condition grouping IDs, task cards, and benchmark partitions. All original rows are retained without intentional measurement corrections or unit conversion. The target remains the source's scaled sound-pressure value. Attribution does not imply endorsement by NASA or the source authors.

Every benchmark specification records its source URL, citation, raw-download hash, retrieval date, derived CSV hash, and transformations. `scripts/curate.py` reproduces the derivation from the original ZIP files; normal evaluation uses immutable checked-in CSV snapshots.
