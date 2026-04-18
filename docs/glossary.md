# Sports Betting Glossary

A reference dictionary for terms that appear throughout this repository's documentation. Terms are grouped by topic area, not alphabetically, so related concepts appear together.

---

## Odds & Probability

**Odds** — A way of expressing the likelihood of an outcome and the payout for a correct bet. Three formats exist (American, decimal, fractional) but they all encode the same information. See [`odds-and-markets.md`](foundations/odds-and-markets.md).

**American odds (moneyline odds)** — Expressed as a positive or negative integer relative to $100. `-110` means bet $110 to win $100. `+150` means bet $100 to win $150. Negative = favorite, positive = underdog.

**Decimal odds** — Common in Europe and Australia. The total return per $1 staked, including your stake back. `2.50` means a $1 bet returns $2.50 (profit of $1.50). Convert to implied probability: `1 / decimal_odds`.

**Fractional odds** — Common in the UK. Written as `numerator/denominator` (e.g., `5/2`). Profit per unit staked = numerator/denominator. A `5/2` bet returns $2.50 profit per $1 staked.

**Implied probability** — The probability the bookmaker's odds imply for an outcome. Calculated by converting odds to a percentage. If the odds imply 55%, the bookmaker believes there is a 55% chance of that outcome. Because of the vig, implied probabilities across all outcomes in a market sum to more than 100%.

**True probability** — The actual (unknown) probability of an outcome. The goal of modeling is to estimate true probability more accurately than the market does.

**Overround (vig, juice, margin)** — The bookmaker's built-in profit margin. Across all outcomes, implied probabilities sum to more than 100% (e.g., 105%). The excess (5%) is the overround. Also called "vig" (short for vigorish) or "juice" in American markets.

**No-vig probability** — Implied probabilities after mathematically removing the bookmaker's margin, giving a fair-market estimate of true probability.

---

## Bet Types & Markets

**Moneyline** — A bet on which team or player wins outright, with no point spread. The simplest bet type.

**Point spread (spread)** — A handicap applied to the favored team to even out the market. Betting the favorite "against the spread" means they must win by more than the spread margin.

**Totals (over/under)** — A bet on whether the combined score of both teams will be over or under a bookmaker-set line.

**Prop bet (proposition bet)** — A bet on a specific event within a game that doesn't directly relate to the final score (e.g., first player to score, total passing yards).

**Parlay** — A single bet that links multiple individual bets. All selections must win for the parlay to pay. Higher potential payout, but much lower probability of winning.

**Teaser** — A parlay variant that lets you adjust point spreads in your favor in exchange for reduced payout.

**Live betting (in-game betting)** — Bets placed after a game has started, with odds that update in real time as the game progresses.

**Opening line** — The first odds posted by a bookmaker for a given event.

**Closing line** — The final odds at the time betting closes (typically game start). Widely considered the most efficient estimate of true probability because it incorporates the most information.

---

## Value & Edge

**Expected value (EV)** — The average outcome of a bet if placed an infinite number of times. A positive-EV bet is profitable in the long run; a negative-EV bet loses money over time. Formula: `EV = (probability_of_win × profit) - (probability_of_loss × stake)`.

**Value bet** — A bet where your estimated probability of winning is higher than the bookmaker's implied probability. If you estimate a 60% chance of winning but the odds only imply 50%, there is positive value.

**Edge** — The percentage advantage your model has over the market. If the market prices an outcome at 50% probability and your model says 55%, your edge is 5 percentage points.

**Positive EV (+EV)** — A bet with positive expected value. The goal of all modeling work is to identify +EV bets consistently.

**Negative EV (-EV)** — A bet with negative expected value. All bets with standard bookmaker vig are -EV unless your probability estimate beats the market.

**Closing line value (CLV)** — The difference between the odds you got when placing a bet and the closing line odds. Consistently beating the closing line is one of the strongest indicators that your model has genuine edge. See [`market-efficiency.md`](foundations/market-efficiency.md).

---

## Model Performance

**Accuracy** — The percentage of predictions where the model correctly identified the winning outcome. A useful but insufficient metric — a model that always picks favorites may have high accuracy but still lose money.

**Calibration** — How well a model's predicted probabilities match actual observed frequencies. A well-calibrated model that says "60% chance" should be correct about 60% of the time. Poorly calibrated models may be accurate but still unprofitable. See [`calibration.md`](modeling/calibration.md).

**Brier score** — A metric that measures the mean squared error between predicted probabilities and actual outcomes (0 or 1). Lower is better. Sensitive to both accuracy and calibration.

**Log-loss (cross-entropy loss)** — A metric that penalizes confident wrong predictions heavily. Better for evaluating probabilistic predictions than simple accuracy.

**Reliability diagram (calibration curve)** — A plot of predicted probability vs. actual observed frequency, used to visually assess how well-calibrated a model is.

**Overfit** — When a model learns the training data too precisely, including noise, and performs poorly on new data. A persistent risk with sports data due to small sample sizes and non-stationarity.

**Lookahead bias** — Using information in your model that would not have been available at the time the prediction was made (e.g., using a player's injury that happened during the game to predict that game's outcome). Invalidates backtests.

---

## Bankroll Management

**Bankroll** — The total amount of money set aside for betting.

**Unit** — A standard bet size, usually expressed as a percentage of the bankroll (e.g., 1 unit = 1–2% of bankroll). Used to make bet sizing comparable across bettors with different bankroll sizes.

**Kelly Criterion** — A mathematical formula for optimal bet sizing that maximizes long-term bankroll growth. `f = (bp - q) / b`, where `b` = odds received, `p` = win probability, `q` = loss probability. See [`bankroll-management.md`](strategy/bankroll-management.md).

**Full Kelly** — Betting the exact fraction of bankroll the Kelly formula recommends. Mathematically optimal but causes extreme variance in practice.

**Fractional Kelly** — Betting a fixed fraction of the full Kelly amount (e.g., ½ Kelly, ¼ Kelly). Reduces variance and drawdown at the cost of slightly slower growth.

**Flat staking** — Betting the same amount (fixed units) on every bet, regardless of perceived edge. Simple and prevents overbetting but ignores edge magnitude.

**ROI (return on investment)** — Total profit divided by total amount wagered, expressed as a percentage. The standard metric for a bettor's long-run performance.

**Yield** — Similar to ROI but typically calculated as profit per unit staked. Used interchangeably with ROI in many contexts.

**Drawdown** — The peak-to-trough decline in bankroll over a period. A measure of downside risk and variance.

**Ruin probability** — The probability that a bettor's bankroll reaches zero. Even with positive EV, aggressive bet sizing can lead to ruin if variance is high.

---

## Statistical & Machine Learning Concepts

**Poisson distribution** — A probability distribution that models the number of events occurring in a fixed time interval when events are independent and occur at a constant rate. Used to model goal-scoring in soccer. See [`models/poisson.md`](modeling/models/poisson.md).

**Elo rating** — A numerical system for estimating relative skill between competitors, updated after each game based on the outcome vs. expectation. See [`models/elo.md`](modeling/models/elo.md).

**Logistic regression** — A statistical model that predicts the probability of a binary outcome (win/loss) from a set of input features. See [`models/logistic-regression.md`](modeling/models/logistic-regression.md).

**Quantile regression** — A regression technique that models a specific quantile (e.g., 25th percentile, 75th percentile) of the outcome distribution rather than just the mean. Useful for spread and totals markets. See [`models/quantile-regression.md`](modeling/models/quantile-regression.md).

**XGBoost** — A gradient-boosted tree algorithm known for strong performance on tabular data. One of the most commonly cited ML methods in sports prediction research.

**Ensemble** — A model that combines predictions from multiple individual models to produce a final prediction. Usually more robust than any single model.

**Feature engineering** — The process of creating and selecting the input variables given to a model. Research consistently shows this matters more than algorithm choice.

**Monte Carlo simulation** — A computational technique that runs thousands of random simulations to estimate a probability distribution over possible outcomes. See [`monte-carlo.md`](modeling/monte-carlo.md).

**Platt scaling** — A post-processing technique that fits a logistic regression on top of a model's raw output scores to improve probability calibration.

**Isotonic regression** — A non-parametric post-processing technique for calibration that fits a monotone function to map raw model scores to calibrated probabilities.

---

## Market Dynamics

**Sharp bettor (sharp)** — A professional or sophisticated bettor whose wagers are large enough to move the line. Bookmakers pay close attention to sharp action.

**Square bettor (square, recreational bettor)** — A casual bettor whose action does not move lines and whose betting patterns tend to be predictable (e.g., betting favorites, betting home teams).

**Line movement** — Changes in the posted odds between opening and closing. Significant line movement often indicates sharp action or important new information (injury news, weather).

**Steam move** — A sudden, coordinated movement in odds across multiple bookmakers, typically driven by sharp syndicate action.

**Reverse line movement** — When the line moves opposite to the direction that public betting percentages would predict. Often a signal of sharp action on the other side.

**Limit** — The maximum amount a bookmaker will accept on a given bet. Sharps are often limited or banned by bookmakers once identified as profitable.

**Market maker** — A bookmaker that sets their own lines independently (e.g., Pinnacle). Their lines are generally considered the most efficient.

**Soft book** — A bookmaker that is slow to adjust lines and accepts large bets from recreational players. Easier to find value at but will often ban or limit winning bettors.

---

## Data & Features

**Historical odds** — Past bookmaker prices for games. Essential for backtesting because you need to know the odds that were actually available, not just post-hoc prices.

**Advanced metrics** — Team or player performance statistics that go beyond simple box scores (e.g., expected goals (xG) in soccer, win shares in basketball, WAR in baseball).

**Expected goals (xG)** — A soccer metric that estimates the probability each shot had of resulting in a goal, based on shot location, angle, and type. More predictive than actual goals scored.

**Rest advantage** — The difference in days of rest between two teams, which can be a predictive feature for game outcomes.

**Line shopping** — Comparing odds across multiple bookmakers to find the best available price for a given bet. Critical for maximizing long-run returns.
