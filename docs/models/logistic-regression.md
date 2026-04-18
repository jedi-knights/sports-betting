# Logistic Regression

Logistic regression is the standard baseline model for binary classification in sports betting — predicting the probability that one team wins a game. It is interpretable, computationally efficient, and well-calibrated out of the box. Despite its simplicity, it is competitive with more complex models when features are well-engineered.

## Why Logistic, Not Linear Regression

A game outcome is binary: win or loss (1 or 0). Linear regression would predict a number on an unbounded scale, producing nonsensical probability estimates like -0.2 or 1.3. Logistic regression maps any input to a value in (0, 1), making it inherently appropriate for probability prediction.

## The Model

### Logistic Function (Sigmoid)

The core transformation that maps a linear combination of features to a probability:

```
σ(z) = 1 / (1 + e^(-z))
```

This function takes any real number `z` and outputs a value between 0 and 1. As `z → +∞`, `σ → 1`. As `z → -∞`, `σ → 0`. At `z = 0`, `σ = 0.5`.

### Prediction

Given features `x₁, x₂, ..., xₙ` with learned coefficients `β₁, β₂, ..., βₙ` and an intercept `β₀`:

```
z = β₀ + β₁x₁ + β₂x₂ + ... + βₙxₙ
P(home_win) = σ(z) = 1 / (1 + e^(-z))
```

### Training Objective

Logistic regression is trained by minimizing log-loss (negative log-likelihood):

```
L = -(1/n) × Σ [y_i × log(p_i) + (1 - y_i) × log(1 - p_i)]
```

Where `y_i` is 1 if the home team won and 0 otherwise, and `p_i` is the predicted probability. This is a proper scoring rule — the globally optimal solution is the true probability, so logistic regression is trained to produce calibrated probabilities. See [`calibration.md`](../calibration.md) for why this matters.

## Feature Inputs for Sports Betting

A minimal but effective feature set:

| Feature | Type | Rationale |
|---------|------|-----------|
| Elo rating difference | Continuous | Compact summary of relative team strength |
| Home/away indicator | Binary | Home advantage is real in all major sports |
| Days since last game | Continuous | Rest advantage, particularly relevant in NBA/NHL |
| Season win % (home team) | Continuous | Recent form in current season |
| Season win % (away team) | Continuous | |
| Season point differential (home) | Continuous | Margin-based form, more predictive than win rate |
| Season point differential (away) | Continuous | |

More features can be added, but marginal returns diminish quickly. Prefer opponent-adjusted metrics over raw statistics. See [`data-and-features.md`](../data-and-features.md).

## Interpreting Coefficients

Logistic regression coefficients are log-odds ratios. A coefficient of `β = 0.5` on a feature means:

- For each 1-unit increase in that feature, the log-odds of a home win increase by 0.5
- The odds ratio is `e^0.5 ≈ 1.65` — the odds increase by 65%

For a feature like "Elo difference," a coefficient of `0.004` means each additional Elo point of advantage increases the log-odds of winning by 0.004. At an Elo difference of 200, the raw log-odds contribution from that feature alone is 0.8, corresponding to approximately 68% win probability (before other features).

This interpretability is one of logistic regression's major advantages over black-box methods like XGBoost — you can audit why the model produced a particular prediction.

## Regularization

Regularization adds a penalty for large coefficients to the training objective, preventing overfitting.

### L2 Regularization (Ridge)

```
L = log_loss + λ × Σ βᵢ²
```

- Shrinks all coefficients toward zero continuously
- Coefficients are rarely exactly zero; all features stay in the model
- Standard choice for most sports betting applications
- Controlled by `λ` (larger = more regularization, smaller coefficients)

### L1 Regularization (Lasso)

```
L = log_loss + λ × Σ |βᵢ|
```

- Can shrink coefficients exactly to zero, performing automatic feature selection
- Useful when you have many candidate features and want a sparse model

### Elastic Net

A combination of L1 and L2. Useful when features are correlated (common with sports statistics).

### Setting the Regularization Strength

Tune `λ` via cross-validation on the training set. Evaluate with log-loss or Brier score on a held-out validation set. See [`backtesting.md`](../backtesting.md).

## Multi-Class Extension

Standard logistic regression is binary (win/lose). For sports with draws (soccer), use multinomial logistic regression (softmax regression):

```
P(home_win) = e^(z_home) / (e^(z_home) + e^(z_draw) + e^(z_away))
P(draw)     = e^(z_draw) / (...)
P(away_win) = e^(z_away) / (...)
```

Three separate linear functions share a single softmax normalization.

## Calibration of Logistic Regression

Logistic regression trained with log-loss tends to be better calibrated than most other classifiers, because the training objective directly incentivizes accurate probability prediction. However:

- Heavy regularization can compress predicted probabilities toward 0.5, causing under-confidence at the extremes
- Feature correlation can cause systematic biases
- Models trained on one time period may be miscalibrated on another

Always evaluate calibration on a held-out set using a reliability diagram. Apply Platt scaling or isotonic regression if systematic bias is detected. See [`calibration.md`](../calibration.md).

## Practical Workflow

1. Collect and clean historical game data
2. Engineer features as rolling/trailing statistics anchored to prediction date (no lookahead bias — see [`backtesting.md`](../backtesting.md))
3. Split data into train/validation/test sets (walk-forward split, not random)
4. Train logistic regression with L2 regularization; tune `λ` on validation set using log-loss
5. Evaluate calibration on validation set; apply calibration fix if needed
6. Evaluate final performance on test set (once only)
7. Compare predicted probabilities against bookmaker implied probabilities to identify value bets

## When to Use Logistic Regression vs. More Complex Models

**Use logistic regression when:**
- You have fewer than ~5,000 historical examples
- Interpretability is a priority
- Your feature set is small and well-chosen
- You are establishing a baseline to validate more complex approaches

**Consider XGBoost or other ML methods when:**
- You have a large feature set with possible non-linear interactions
- Sample size is large enough to learn interactions reliably
- Logistic regression is already performing near its ceiling

In practice, logistic regression with good features is often competitive with or superior to XGBoost for sports outcomes, because sports datasets are relatively small and the signal-to-noise ratio is low. The additional complexity of tree-based methods can hurt more than it helps. See [`models/ml-methods.md`](ml-methods.md) for a direct comparison.
