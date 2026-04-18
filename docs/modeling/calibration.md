# Calibration

Calibration is the most important property of a sports betting model and the most underappreciated. A 2024 meta-analysis found that calibration-optimized models returned +34.69% on investment vs. -35.17% for accuracy-optimized models — a gap of nearly 70 percentage points. Understanding why requires understanding what calibration is and how it differs from accuracy.

## What Calibration Means

A model is well-calibrated if its predicted probabilities match observed frequencies.

If your model says "60% probability of a home win" across 1,000 games, approximately 600 of those games should result in a home win. If only 480 win (48%), your model is overconfident — it assigned 60% when the true rate was 48%. If 720 win (72%), your model is underconfident.

More formally: for every predicted probability `p`, the fraction of events where the outcome actually occurred should equal `p`.

## Why Accuracy Is Not Enough

A model can be highly accurate while being completely miscalibrated. Consider a model that predicts the probability of every NFL home team winning as 55% (which is roughly the empirical home-win rate). This model will be correct about 55% of the time — but it will never identify a value bet because it assigns no game a probability meaningfully above or below the market's implied probability.

Worse, a model that is accurate but overconfident will identify false edges. If the model says "75% chance" but the true rate is 60%, you will bet into situations where the market's 65% implied probability is actually closer to the truth — and you will lose money despite "high accuracy."

## Visualizing Calibration: The Reliability Diagram

A reliability diagram (also called a calibration curve) plots:
- X-axis: predicted probability buckets (e.g., 0.0–0.1, 0.1–0.2, ..., 0.9–1.0)
- Y-axis: actual observed frequency within each bucket

A perfectly calibrated model produces a straight diagonal line from (0,0) to (1,1). Deviations from this diagonal reveal systematic biases:

- **Curve above the diagonal**: model is underconfident. Predictions of "60%" correspond to outcomes that occur more than 60% of the time.
- **Curve below the diagonal**: model is overconfident. Predictions of "60%" correspond to outcomes that occur less than 60% of the time.
- **S-shaped curve**: a common pattern in models trained to maximize accuracy — they cluster predictions in the middle and underestimate extreme probabilities.

## Calibration Metrics

### Brier Score

Mean squared error between predicted probability and actual outcome (0 or 1):

```
Brier Score = (1/n) × Σ (p_i - o_i)²
```

Where `p_i` is the predicted probability and `o_i` is 1 if the event occurred, 0 if not.

- Range: 0 (perfect) to 1 (worst possible)
- A Brier score of 0.25 corresponds to random 50/50 guessing
- Sensitive to both discrimination (can the model separate outcomes?) and calibration (are the probabilities accurate?)

### Log-Loss (Cross-Entropy)

```
Log-Loss = -(1/n) × Σ [o_i × log(p_i) + (1-o_i) × log(1-p_i)]
```

Log-loss heavily penalizes confident wrong predictions. A model that says "99% probability" for an event that doesn't occur suffers a massive log-loss penalty. This makes it excellent for evaluating betting models where probability accuracy matters enormously.

### Expected Calibration Error (ECE)

Divides predictions into bins and measures the weighted average deviation between predicted probability and observed frequency across all bins:

```
ECE = Σ_b (|b|/n) × |observed_frequency(b) - average_predicted_prob(b)|
```

Lower is better. ECE provides a single scalar summary of calibration quality.

## Why Miscalibration Causes Losses

Suppose a bookmaker prices Team A at 50% implied probability (after removing vig). Your model says 60%. You bet.

But if your model is overconfident and 60% really means the true probability is 52%, you have only a small edge. If your bet sizing (e.g., Kelly Criterion) is based on a false 60%, you are overbetting significantly, which accelerates drawdown.

Worse: if your model's 60% corresponds to a true rate of 45%, you are now actively betting into negative-EV situations while believing they are positive. This is the failure mode that produces the -35.17% ROI found in accuracy-optimized models.

## Post-Hoc Calibration Methods

These techniques are applied after a model is trained to improve its probability estimates without retraining.

### Platt Scaling

Fits a logistic regression on top of the model's raw output scores:

```
calibrated_p = 1 / (1 + exp(-(A × score + B)))
```

Parameters A and B are learned from a held-out calibration set. Simple, fast, and works well when the miscalibration is roughly sigmoidal.

**Best for**: SVMs, neural networks, any model producing raw decision scores.

**Limitation**: assumes the miscalibration has a specific sigmoidal shape.

### Isotonic Regression

Fits a monotone non-decreasing step function from raw scores to observed frequencies. More flexible than Platt scaling — it makes no assumptions about the shape of miscalibration.

**Best for**: gradient-boosted trees (XGBoost, LightGBM), Random Forests.

**Limitation**: requires more calibration data than Platt scaling to avoid overfitting.

### Temperature Scaling

A variant of Platt scaling with a single parameter (temperature T) that scales all logits uniformly:

```
calibrated_p = softmax(z / T)
```

Popular in deep learning because it preserves rank ordering while adjusting the sharpness of predictions.

## Training for Calibration

Rather than applying post-hoc fixes, you can train models with calibration in mind from the start:

1. **Use log-loss as the training objective** — models trained with cross-entropy loss tend to be better calibrated than those trained for accuracy (accuracy loss is non-differentiable and gradient-unfriendly for probabilities).

2. **Avoid excessive regularization** — heavy L2 regularization in logistic regression pushes predictions toward 0.5, causing underconfidence at the extremes.

3. **Regularize calibration directly** — some frameworks allow adding a calibration penalty term to the loss function.

4. **Use proper scoring rules** — Brier score and log-loss are "proper" scoring rules, meaning a model maximizing them is incentivized to produce true probabilities, not just binary predictions.

## Calibration vs. Discrimination

These are two distinct properties:

- **Discrimination**: can the model correctly rank outcomes? (AUC-ROC measures this)
- **Calibration**: are the predicted probabilities accurate? (Reliability diagrams, ECE, Brier score)

A model can have excellent discrimination but poor calibration — it correctly identifies which team is more likely to win but assigns probabilities of 85% to games it should say are 65%. For betting, you need both: discrimination to find edges and calibration to size bets correctly.

## Practical Workflow

1. Train your model using log-loss as the objective
2. Evaluate calibration on a held-out validation set using a reliability diagram and ECE
3. If miscalibration is evident, apply Platt scaling (for most models) or isotonic regression (for tree-based models)
4. Re-evaluate on a separate test set (not the calibration set)
5. Monitor calibration on live data — it degrades as the underlying game dynamics change (player movement, rule changes, coaching staff turnover)

## Key Takeaways

- Accuracy tells you how often your model picks the right team. Calibration tells you whether your probability estimates are trustworthy.
- Only calibrated probability estimates can identify true value bets. Miscalibrated models identify false edges.
- Post-hoc calibration (Platt scaling, isotonic regression) is almost always worth applying to any non-logistic-regression model.
- Treat calibration as an ongoing measurement, not a one-time check — it drifts as the sport evolves.
