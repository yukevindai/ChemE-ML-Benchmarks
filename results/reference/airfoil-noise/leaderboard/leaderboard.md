# Airfoil noise under chord-length extrapolation

Data: empirical. Metric: group_mae (dB); lower is better.

| Rank | Method | Seeds | Test mean | Seed SD |
| --- | --- | --- | --- | --- |
| 1 | random_forest | [0, 1, 2] | 2.52463 | 0.06895080755650713 |
| 2 | ridge | [0, 1, 2] | 3.66878 | 0.0 |
| 3 | mean | [0, 1, 2] | 5.396 | 0.0 |

Generalization: Prediction at chord lengths >0.2286 m, with validation at (0.1524,0.2286] m and training <=0.1524 m, within the supplied NACA 0012 collection.

Limitations:

- No documented run, specimen, laboratory or publication IDs; condition groups cannot certify independent experimental replicates.
- NACA 0012 geometry family, source apparatus, span and observer settings limit transfer; this does not test arbitrary airfoils or transport laws.
- Target is the source's scaled sound-pressure value in dB, not an unscaled acoustic pressure or sound-power estimate.
- Seed standard deviation measures algorithm variation, not experimental uncertainty.
- This local public-data leaderboard validates scores, not honest training or absence of test-set tuning.
- Ranks compare this exact task only; metrics from different targets, units, or splits must not be pooled.
