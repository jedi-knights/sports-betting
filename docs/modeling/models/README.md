# Models

Detailed implementation guides for each modeling approach used in sports betting. Each document covers the mathematical foundation, implementation steps, recommended feature inputs, known limitations, and when to prefer one approach over another.

These documents assume you have read [Calibration](../calibration.md) and [Backtesting](../backtesting.md) from the parent [Modeling](../README.md) section — calibration in particular determines how you evaluate any model you build.

## Models

### [Poisson Distribution](poisson.md)

**Best for**: Soccer (all markets), NHL goals, MLB runs

Models goal or run scoring as an independent Poisson process for each team, then combines the two distributions into a full scoreline probability matrix. From that matrix you can derive 1X2 (home/draw/away) probabilities, over/under totals, correct-score market prices, and Asian handicap lines — all from a single set of estimated parameters.

Key topics:
- Estimating attack and defense strength ratings from historical results
- The Dixon-Coles correction for low-scoring game states (the 0-0, 1-0, 0-1, and 1-1 outcomes are systematically underestimated by the naive model)
- Time-decay weighting to handle mid-season team quality changes
- Application to NHL and MLB beyond soccer

The Poisson model is the foundational approach for any sport where scoring is infrequent and discrete. It is mechanistic and interpretable, and produces the full distribution of outcomes rather than just a win probability.

---

### [Elo Rating System](elo.md)

**Best for**: Relative team strength estimation in any sport; useful as a baseline feature in larger models

Assigns every team a single numeric rating, updated after each game based on the outcome relative to expectation. The rating difference between two teams directly produces a win probability via a logistic function. Simple, robust, and effective at capturing team quality even with limited data early in a season.

Key topics:
- The expected score formula and rating update rule
- K-factor selection and tuning by sport
- Home advantage adjustment (typically +65 points in NFL, +100 in NBA)
- Margin-of-victory multiplier (improves predictive power significantly)
- Between-season regression to the mean
- Using Elo as a feature in larger regression or ML models rather than as a standalone predictor

Elo is rarely the best standalone predictor but is almost always worth including as a feature because it provides a compact, robust strength estimate that handles small samples better than rolling statistics.

---

### [Logistic Regression](logistic-regression.md)

**Best for**: Win probability modeling; the standard baseline for any new sport or market

Maps a linear combination of features through a logistic (sigmoid) function to produce a probability in (0,1). Trained by minimizing log-loss, which directly incentivizes calibrated probability output. The most interpretable model in this directory — every coefficient has a clear interpretation as a log-odds ratio.

Key topics:
- Why logistic regression rather than linear regression for binary outcomes
- The training objective (log-loss) and why it produces better-calibrated probabilities than accuracy-optimized models
- L1 vs. L2 regularization and when to use each
- Multinomial extension for three-outcome markets (soccer 1X2)
- Practical workflow: feature engineering → train/validate/test split → calibration check → deployment
- When logistic regression beats XGBoost (spoiler: more often than you'd expect)

This is the recommended first model to build. Before adding complexity, establish a well-calibrated logistic regression baseline and prove that more complex models improve on it out-of-sample.

---

### [Quantile Regression](quantile-regression.md)

**Best for**: Spread and totals markets in any sport; any market where you need the full outcome distribution rather than just the mean

Standard regression predicts the mean outcome. Quantile regression predicts a specific percentile of the outcome distribution — e.g., the 75th percentile of total points in an NBA game. By training models at multiple quantiles, you recover the full predicted CDF, which lets you price any totals line, not just the one you trained on.

Key topics:
- The pinball (check) loss function and how it targets a specific quantile
- Building a full CDF from multiple quantile models
- Application to NFL spreads and NBA totals
- Quantile Regression Forests: a non-parametric extension that captures non-linear feature interactions
- Gradient boosting with quantile loss (XGBoost and LightGBM both support this natively)
- The crossing quantiles problem and how to fix it

The key research finding cited in the repository's README — "point spreads explain 86% of outcome variability" — is the context for why quantile regression is valuable here: knowing the mean margin of victory is not sufficient for pricing spread markets accurately.

---

### [Machine Learning Methods](ml-methods.md)

**Best for**: Large feature sets with potential non-linear interactions; ensembling with logistic regression

Covers XGBoost (gradient-boosted trees), Random Forests, neural networks, and ensemble approaches. XGBoost leads reported accuracy benchmarks at 91–94%, but the research consistently finds that feature engineering matters more than algorithm choice.

Key topics:
- Why XGBoost works well on sports tabular data (non-linear interactions, missing value handling, built-in regularization)
- Critical hyperparameters and their effects (max_depth, learning_rate, subsample)
- Why tree-based models need post-hoc calibration (isotonic regression) despite being trained with log-loss
- Random Forests: when they are preferred (quantile estimation, easier tuning)
- Neural networks: where they add value (high-dimensional unstructured inputs) vs. where they don't (standard tabular sports data)
- Ensemble approaches: combining logistic regression and XGBoost typically outperforms either alone
- The feature importance ceiling: switching from logistic regression to XGBoost with the same features typically improves accuracy by 2–3%; adding better features improves it by 6–8%

## Choosing a Model

| Situation | Recommended approach |
|-----------|---------------------|
| First model in a new sport | Logistic regression |
| Soccer goal/scoreline markets | Poisson + Dixon-Coles |
| Spread or totals distribution | Quantile regression |
| Relative team strength feature | Elo (as an input feature) |
| Large feature set, want to capture interactions | XGBoost, calibrated with isotonic regression |
| Best overall performance | Ensemble: logistic regression + XGBoost |

## Relationship to Other Documents

- All models should be evaluated using the metrics in [Backtesting](../backtesting.md)
- All models should be calibration-checked using the methods in [Calibration](../calibration.md)
- Features fed into these models come from [Data and Features](../data-and-features.md)
- Sport-specific model recommendations are in [Sport-Specific guides](../../sport-specific/README.md)
