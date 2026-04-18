# Machine Learning Methods

Machine learning approaches — particularly gradient-boosted trees — have reported the highest raw accuracy in sports prediction research, with XGBoost achieving 91–94% accuracy on select datasets. However, accuracy alone is not the right objective for betting. This document covers the major ML methods, when to use them, and what research has actually found about their relative performance.

## The Research Landscape

Sports prediction research consistently reports the following findings:

1. **XGBoost and Random Forests lead on accuracy**: gradient-boosted and ensemble tree methods outperform classical statistical approaches on most reported accuracy benchmarks.
2. **Feature engineering matters more than algorithm choice**: teams that invested in better features saw larger improvements than those that switched algorithms.
3. **Calibration is underreported**: most academic papers optimize for accuracy (AUC, F1, hit rate) rather than calibration. This makes the results difficult to translate directly to betting profitability. See [`calibration.md`](../calibration.md).

## XGBoost

XGBoost (Extreme Gradient Boosting) is a gradient-boosted decision tree algorithm. It builds an ensemble of weak learners (shallow trees) sequentially, where each tree corrects the errors of the previous ones.

### Why It Works Well on Sports Data

- **Non-linear interactions**: automatically captures relationships between features that linear models miss (e.g., rest advantage matters more when traveling across time zones)
- **Handles mixed feature types**: works natively with continuous, discrete, and binary features without preprocessing
- **Robust to feature scale**: does not require feature normalization
- **Built-in regularization**: L1 and L2 penalties in the objective function reduce overfitting
- **Missing value handling**: can learn to route missing values during tree construction

### Key Hyperparameters

| Parameter | Effect | Typical range |
|-----------|--------|---------------|
| `n_estimators` | Number of trees | 100–1000 |
| `max_depth` | Maximum tree depth | 3–6 (shallow trees generalize better) |
| `learning_rate` | Step size (shrinkage) | 0.01–0.3 (lower = more trees needed but better generalization) |
| `subsample` | Fraction of training data per tree | 0.6–0.9 (prevents overfitting) |
| `colsample_bytree` | Fraction of features per tree | 0.6–0.9 |
| `min_child_weight` | Minimum instance weight in leaf | 3–10 (higher = more conservative trees) |

### Calibration Requirement

XGBoost is trained to minimize log-loss by default, which encourages calibration, but tree-based models are known to produce poorly calibrated probabilities — they tend to cluster predictions near the middle of the probability range. Always apply isotonic regression calibration after training. See [`calibration.md`](../calibration.md).

### Training Example (Conceptual)

```python
# Features: Elo difference, home/away, rest, rolling stats, etc.
# Target: home team won (1) or not (0)

model = XGBClassifier(
    n_estimators=500,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='binary:logistic',
    eval_metric='logloss'
)

model.fit(X_train, y_train,
          eval_set=[(X_val, y_val)],
          early_stopping_rounds=50)
```

## Random Forests

Random Forests build many decision trees in parallel on bootstrapped subsets of the data, each tree also seeing a random subset of features. The final prediction is the average (or majority vote) of all trees.

### Differences from XGBoost

- **Parallel, not sequential**: trees are independent, making Random Forests parallelizable
- **Often slightly lower accuracy than XGBoost**: boosting's sequential error correction typically outperforms bagging for structured data
- **Better for quantile estimation**: Quantile Regression Forests (see [`models/quantile-regression.md`](quantile-regression.md)) are built on Random Forests
- **Less hyperparameter sensitivity**: generally easier to get reasonable results without extensive tuning

### Feature Importance

Random Forests (and XGBoost) provide feature importance scores — estimates of how much each feature contributed to predictions. Common measures:

- **Gain**: total improvement in loss attributable to splits on that feature (XGBoost default)
- **Permutation importance**: performance drop when a feature's values are randomly shuffled
- **SHAP values**: game-theory-based attribution providing consistent, additive importance scores (recommended for interpretability)

Use feature importance as a diagnostic tool, not a definitive ranking. High-importance features in one dataset may not generalize.

## Neural Networks

Deep learning has made limited inroads into sports outcome prediction for tabular data. Research typically shows neural networks performing comparably to XGBoost but requiring substantially more data and tuning.

### Where Neural Networks Add Value

- **High-dimensional unstructured inputs**: player tracking coordinates, video frames, or text (natural language)
- **Sequential data**: LSTM or Transformer models that capture game state trajectories
- **Very large datasets**: when sample size exceeds tens of thousands of games (rare for any single sport and league)

For standard sports prediction from box scores and team statistics, XGBoost almost universally matches or outperforms deep learning with far less infrastructure cost.

## Ensemble Methods

Rather than choosing one model, ensemble approaches combine predictions from multiple models. The most common approach in sports betting:

1. Train logistic regression, XGBoost, and Random Forest models separately
2. Combine predictions using a simple average or a trained meta-learner (stacking)
3. Evaluate the ensemble against each individual model on a held-out test set

Ensembles reduce variance by averaging out individual model errors. The gain is largest when the component models make different types of errors — a logistic regression (linear decision boundary) and XGBoost (non-linear) often complement each other.

## Comparative Performance Summary

Based on reported results across multiple studies:

| Method | Accuracy | Calibration | Interpretability | Data requirement |
|--------|---------|-------------|-----------------|-----------------|
| Logistic regression | Moderate | Good | High | Low |
| Random Forest | High | Moderate | Low | Moderate |
| XGBoost | Highest | Moderate | Low | Moderate |
| Neural Network | High | Varies | Very low | High |
| Ensemble | Highest (typically) | Good | Very low | Moderate |

**Important caveat**: these accuracy figures come from papers that optimize for prediction accuracy, not betting profitability. After post-hoc calibration and evaluation against bookmaker odds, the practical differences between well-tuned versions of these models narrow considerably.

## The Feature Engineering Ceiling

Research consistently finds that beyond a certain point, algorithm choice has diminishing impact compared to feature quality. In one representative study, switching from logistic regression to XGBoost with the same features improved accuracy by 2–3 percentage points, while adding opponent-adjusted metrics improved accuracy by 6–8 percentage points on the same baseline model.

The implication: before spending time tuning model architecture, ensure your feature set includes:
- Opponent-adjusted team strength metrics
- Rest and travel differentials
- Injury-adjusted performance estimates
- Recent form (rolling windows) rather than season-to-date averages

## Practical Starting Point

For a new sports betting model:

1. Start with logistic regression as a well-calibrated baseline
2. Add XGBoost as a second model; compare calibrated probabilities on a held-out validation set
3. If XGBoost outperforms after calibration, use it; if not, the simpler model is preferable
4. Consider a simple ensemble (average of the two) as a final model

Do not jump directly to neural networks or complex architectures before establishing that simpler methods are insufficient. See [`models/logistic-regression.md`](logistic-regression.md) for a detailed baseline implementation.
