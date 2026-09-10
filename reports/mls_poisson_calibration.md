# MLS Poisson Calibration Report

- **Data**: `data/mls_full.csv`
- **Model**: Poisson (Dixon-Coles) wrapped in isotonic calibrator
- **Predictions graded**: 4738 (walk-forward, min_train=200)

## Summary metrics

| Metric | Value | Reference |
|---|---:|---|
| Brier score | 0.2528 | 0 = perfect, 0.25 = random coin flip |
| Log loss | 0.7949 | Lower is better; unbounded above |
| ECE | 0.0435 | 0 = perfectly calibrated |

## Reliability diagram (home-win probability)

Each row is a bin of predicted home-win probability.
`observed` should track `predicted` for a well-calibrated model.

| Predicted (bin center) | Observed frequency | Games in bin |
|---:|---:|---:|
| 0.008 | 0.286 | 28 |
| 0.148 | 0.412 | 34 |
| 0.249 | 0.481 | 52 |
| 0.359 | 0.444 | 180 |
| 0.460 | 0.484 | 1924 |
| 0.536 | 0.507 | 1941 |
| 0.638 | 0.555 | 411 |
| 0.739 | 0.633 | 98 |
| 0.831 | 0.692 | 39 |
| 0.972 | 0.677 | 31 |

## Interpretation

A Brier score of 0.25 is the coin-flip baseline for a 3-way market when graded on home-win only. Values meaningfully below 0.25 indicate the model is extracting signal beyond the base rate.

ECE below 0.05 typically indicates the isotonic wrapper is doing its job. Larger values point at systematic over- or under-confidence in specific probability ranges — inspect the reliability table above to see which bins diverge from the diagonal.
