# Catalog coverage

| Domain | Empirical benchmark | Synthetic software fixture |
| --- | --- | --- |
| Batteries | Pending dataset/provenance admission | Retention and lifetime |
| Electrolytes | Pending dataset/provenance admission | Conductivity response |
| Adsorption | Pending dataset/provenance admission | Simplified isotherm |
| Catalysis | Pending dataset/provenance admission | Conversion response |
| Separations | Pending dataset/provenance admission | Simplified purity response |
| Thermodynamics | Pending dataset/provenance admission | Gas molar volume |
| Transport phenomena | Airfoil self-noise | Pipe-flow response |
| Materials properties | Concrete compressive strength | Porosity/modulus response |
| Process optimization | Pending dataset/provenance admission | Process objective prediction; not an optimization-policy benchmark |

Each synthetic fixture uses 20 mathematical families and five related design points per family. Official assignments hold out complete families: 60 training, 20 validation and 20 test rows. There is no measurement noise model, experimental provenance, or claim of physical completeness. The toy equations and seeds are visible in `scripts/curate.py`.

The empirical tasks contain 2,533 published rows in total. No empirical rows are silently replaced with synthetic values, and empirical/synthetic status is carried through task cards, prepared manifests and individual leaderboard reports. A cross-task numerical leaderboard is intentionally undefined because targets and units differ.
