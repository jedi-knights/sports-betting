# Poisson Distribution Model

The Poisson model is the classical statistical approach for sports where scoring occurs as discrete, infrequent events — most notably soccer. It models each team's goal-scoring as an independent Poisson process and combines those distributions to compute the probability of any specific scoreline.

## The Poisson Distribution

A Poisson distribution models the number of events occurring in a fixed time interval when:
1. Events occur independently of each other
2. The average rate of events is constant

The probability of observing exactly `k` events when the expected rate is `λ`:

```
P(X = k) = (e^(-λ) × λ^k) / k!
```

Where `e ≈ 2.718` (Euler's number) and `k! = k × (k-1) × ... × 1`.

For soccer: if a team is expected to score an average of 1.5 goals in a game, then `λ = 1.5`. The Poisson distribution gives us:

| Goals | Probability |
|-------|-------------|
| 0 | 22.3% |
| 1 | 33.5% |
| 2 | 25.1% |
| 3 | 12.6% |
| 4 | 4.7% |
| 5+ | 1.7% |

## Applying Poisson to Soccer Match Prediction

### Step 1: Estimate Expected Goals for Each Team

The most common approach uses historical attack and defense strength ratings:

```
λ_home = home_attack_strength × away_defense_weakness × home_advantage × league_avg_home_goals
λ_away = away_attack_strength × home_defense_weakness × league_avg_away_goals
```

Where:
- **Attack strength** = team's goals scored / league average goals scored (per game)
- **Defense weakness** = goals conceded / league average goals conceded (per game)
- **Home advantage factor**: typically 1.2–1.4 depending on the league

### Step 2: Compute the Scoreline Probability Matrix

Because we assume home and away goals are independent, the probability of any scoreline `(i, j)` is:

```
P(home_goals = i, away_goals = j) = Poisson(i; λ_home) × Poisson(j; λ_away)
```

This produces a matrix where each cell is the probability of a specific final score:

```
         Away goals
         0     1     2     3
Home  0  0.05  0.07  0.05  0.02
goals 1  0.08  0.11  0.08  0.03
      2  0.06  0.09  0.06  0.02
      3  0.04  0.05  0.04  0.01
```

### Step 3: Aggregate Scorelines into Market Outcomes

From the matrix, compute:
- **Home win probability**: sum of all cells where home_goals > away_goals
- **Draw probability**: sum of diagonal cells (home_goals = away_goals)
- **Away win probability**: sum of all cells where away_goals > home_goals
- **Over/under totals**: sum of cells where total goals exceed (or fall below) a line
- **Correct score**: individual cell values become correct-score market probabilities

## Attack and Defense Strength Estimation

### Dixon-Coles Method (1997)

The foundational paper for Poisson soccer models. Dixon and Coles proposed:

1. Estimating team attack and defense parameters by maximum likelihood on historical results
2. A correction factor `ρ` (rho) that adjusts the probabilities for 0-0, 1-0, 0-1, and 1-1 scorelines — these occur more frequently than the independent Poisson model predicts

The rho correction accounts for the slight negative correlation between team scores (if one team scores, the other has less time/opportunity):

```
P(0,0) = Poisson(0; λ_home) × Poisson(0; λ_away) × τ(0, 0, λ_home, λ_away, ρ)
P(1,0) = Poisson(1; λ_home) × Poisson(0; λ_away) × τ(1, 0, λ_home, λ_away, ρ)
P(0,1) = Poisson(0; λ_home) × Poisson(1; λ_away) × τ(0, 1, λ_home, λ_away, ρ)
P(1,1) = Poisson(1; λ_home) × Poisson(1; λ_away) × τ(1, 1, λ_home, λ_away, ρ)
```

The Dixon-Coles model significantly improves calibration over the naive independent Poisson, particularly for correct-score markets.

### Time-Decay Weighting

Team attack and defense strength changes over a season due to transfers, injuries, and form. Incorporating time-decay weighting in the parameter estimation gives more weight to recent matches:

```
weight(t) = exp(-ξ × (T - t))
```

Where `T` is the current date, `t` is the match date, and `ξ` (xi) is a decay parameter. Typical values: `ξ ≈ 0.002` (roughly a half-life of ~350 days).

## Extending to Other Sports

### Hockey (NHL)

Hockey goal-scoring is approximately Poisson, making this approach directly transferable. Adjustments needed:
- Overtime and shootout outcomes require separate modeling
- Goaltender quality is a dominant factor that needs explicit representation

### Basketball

Basketball scoring is too high-frequency and continuous for the raw Poisson model to be appropriate. The total points in a game can be modeled as Normal (Gaussian) distributed, but for point spread markets, team strength differences and pace adjustments matter more than count distributions.

### Baseball

Runs per game in baseball follow a distribution that is close to Poisson (discrete, infrequent scoring events, relatively constant rate). Baseball run-scoring models use pitching matchups as the primary driver of expected runs.

## Limitations

**Independence assumption**: the model assumes home and away goals are independent. In practice, game state introduces dependencies — a team that falls behind often changes tactics, affecting both teams' scoring rates. The Dixon-Coles correction addresses the most extreme cases (low-scoring games) but does not fully resolve the issue.

**Stationarity**: the model assumes team strengths are stable. In reality, they change mid-season. Time-decay weighting partially addresses this.

**Squad rotation**: Poisson parameters are estimated from historical team data, but heavily rotated lineups (common in cup competitions) perform differently from full-strength ones. The model has no mechanism to account for this without additional lineup-adjusted inputs.

**Market for correct scores**: bookmakers are aware of the Poisson model and price correct-score markets accordingly. The most accessible edges are in less-obvious scoreline combinations and in markets where your λ estimates differ meaningfully from the bookmaker's.

## Resources

- Dixon, M.J. and Coles, S.G. (1997) "Modelling Association Football Scores and Inefficiencies in the Football Betting Market." *Journal of the Royal Statistical Society: Series C*, 46(2), 265–280. — The foundational paper.
- Maher, M.J. (1982) "Modelling Association Football Scores." *Statistica Neerlandica*, 36(3), 109–118. — Earlier work that Dixon-Coles builds on.
