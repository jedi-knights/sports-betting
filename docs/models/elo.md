# Elo Rating System

The Elo rating system is a method for estimating the relative skill of competitors in a zero-sum game. Originally developed by Arpad Elo for chess in the 1960s, it has been adapted for virtually every team and individual sport. Elo ratings serve two roles in sports betting: as a standalone win probability estimator and as a strength feature within larger models.

## How Elo Works

Every team starts with a rating (typically 1500 for a new entrant). After each game, ratings are updated based on the outcome relative to expectation: a win against a strong opponent gains more rating points than a win against a weak one.

### Expected Score (Win Probability)

Given ratings `R_A` and `R_B` for Team A and Team B:

```
E_A = 1 / (1 + 10^((R_B - R_A) / 400))
E_B = 1 - E_A
```

This is a logistic function of the rating difference. The `400` is a scaling factor: a team 400 points above its opponent is expected to win approximately 91% of the time.

### Rating Update

After a game with actual outcome `S_A` (1 for win, 0.5 for draw, 0 for loss):

```
R_A_new = R_A + K × (S_A - E_A)
R_B_new = R_B + K × (S_B - E_B)
```

Where `K` is the K-factor — the maximum rating change per game.

### The K-Factor

The K-factor controls how quickly ratings respond to new results. Higher K = faster adaptation, more volatile ratings. Lower K = more stable ratings, slower to reflect recent form changes.

Common K-factor choices by sport:

| Sport | K-factor | Rationale |
|-------|---------|-----------|
| Chess (beginners) | 32 | New players need fast convergence |
| Chess (masters) | 10 | Established players should be stable |
| NFL (FiveThirtyEight) | 20 | Moderate volatility for 16-game season |
| NBA (FiveThirtyEight) | 20 | Similar |
| Soccer | 20–40 | Varies by implementation |
| Tennis (individual) | 32–64 | Higher because individual results are decisive |

K-factor tuning is typically done by minimizing prediction error (log-loss or Brier score) on held-out data.

## Home Advantage Adjustment

Elo ratings estimate intrinsic team strength, but home teams win at a higher rate across all sports. The standard approach adds a fixed offset to the home team's effective rating before computing expected score:

```
E_home = 1 / (1 + 10^((R_away - (R_home + home_advantage)) / 400))
```

Common home advantage values in Elo points:
- NFL: ~65 points
- NBA: ~100 points
- Soccer (varies by league): 60–120 points
- MLB: ~25 points (smaller home advantage empirically)

Home advantage adjustments should not be applied to neutral-site games (playoffs, Super Bowl, World Cup).

## Margin of Victory Adjustment

Standard Elo only cares whether you won or lost, not by how much. This throws away information. A blowout win is more informative than a 1-point squeaker.

FiveThirtyEight's NFL Elo model uses a margin-of-victory multiplier:

```
MoV_multiplier = ln(|margin| + 1) × (2.2 / (|Elo_winner - Elo_loser| × 0.001 + 2.2))
```

The second factor is an "autocorrelation correction" that reduces the multiplier for games where the winner was already heavily favored — blowing out a weak team should earn fewer points than blowing out a strong one.

Margin-adjusted Elo ratings tend to be more predictive early in a season when sample sizes are small.

## Regression to the Mean

Between seasons, team Elo ratings are typically pulled toward the league mean (1500) by a fixed amount:

```
R_new_season = R_end_of_season × (1 - regress_factor) + 1500 × regress_factor
```

Common regression factors:
- NFL: 1/3 regression (FiveThirtyEight)
- NBA: smaller regression due to roster continuity
- Soccer: varies; accounts for promotions/relegations by resetting newly promoted teams closer to mean

Regression captures the fact that rosters turn over and extreme performances tend to regress.

## Travel and Rest Adjustments

For sports with back-to-back games or significant travel, additional adjustment factors can be applied to the effective rating:

```
effective_R = base_R + home_advantage - travel_penalty - back_to_back_penalty
```

These adjustments improve calibration for games where fatigue is a meaningful factor (most relevant in NBA and NHL).

## Using Elo Ratings as Model Features

Elo ratings are often used not as a standalone prediction but as one feature among many in a larger regression or machine learning model:

- **Elo difference**: `R_home - R_away` — the primary strength differential signal
- **Home team Elo**: absolute team quality matters for total scoring environments
- **Rate of change**: recent rating trajectory (is the team improving or declining?)
- **Pre-season Elo**: captures off-season roster changes before in-season Elo has converged

In this role, Elo provides a compact, single-number summary of relative team strength that is robust to small sample sizes early in a season.

## Limitations

**Slow convergence at season start**: Elo ratings do not incorporate off-season information. A team that significantly upgraded their roster over the summer starts the season with a misleading rating. Supplement with pre-season adjustments (roster quality estimates, coaching changes) or use the previous season's closing rating as a prior.

**No within-game information**: Elo updates only after the game ends. It cannot capture lineup changes, injuries, or game states that mid-game live betting requires.

**Sport-specific structural issues**: 
- In soccer, draws present a challenge — Elo was designed for binary outcomes. The standard approach is to give 0.5 to each team for a draw, but this conflates a 0-0 draw (defensive game) with a 3-3 draw (high-scoring game).
- In baseball, pitcher matchup dominates outcome probability in ways that a team-level Elo cannot capture without pitcher-specific adjustments.

**Ignores margin context**: standard Elo only knows win/loss/draw, not how the game unfolded. Two teams can have identical Elo ratings despite one consistently winning by large margins while the other keeps winning by one point.

## Further Reading

- FiveThirtyEight's Elo methodology is publicly documented and a good starting reference for NFL and NBA implementations.
- Hvattum and Arntzen (2010) provide a systematic comparison of Elo variants for soccer prediction.
