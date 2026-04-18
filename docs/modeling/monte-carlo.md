# Monte Carlo Simulation

Monte Carlo simulation is a computational technique that uses repeated random sampling to estimate probability distributions over outcomes. In sports betting, it is used to answer questions that analytical formulas cannot easily handle: What is the probability distribution of total points scored? What are the odds that a team wins the championship given current standings? What spread value maximizes model edge?

## The Core Idea

When the analytical probability distribution of an outcome is too complex to compute exactly, you can approximate it by simulating the event thousands or millions of times and observing the resulting distribution.

For example: computing the probability that Team A wins a best-of-7 series given per-game win probabilities is analytically solvable but tedious. A Monte Carlo simulation does it in milliseconds with arbitrary precision.

## Basic Structure

```
results = []
for i in range(N_SIMULATIONS):
    outcome = simulate_single_game()
    results.append(outcome)

probability_of_event = count(results where event occurred) / N_SIMULATIONS
```

The accuracy of the estimate improves with the number of simulations. For sports betting applications, 10,000–100,000 simulations typically provides sufficient precision (standard error < 0.5%).

## Applications in Sports Betting

### 1. Totals and Over/Under Markets

The most direct application. Given a probability distribution over the possible total score of a game (e.g., from a Poisson model for soccer or a historical distribution for NBA games), Monte Carlo can estimate:

- The probability that total points exceed any given line
- The fair-odds line (the total at which over and under are 50/50)
- The sensitivity of the probability to the score distribution parameters

This is especially useful when the score distribution is non-symmetric or when you want to price multiple totals lines simultaneously.

### 2. Correct-Score Markets (Soccer)

Soccer correct-score markets price individual final scorelines (e.g., "2-1 home win"). With Poisson-distributed home and away goals (see [`models/poisson.md`](models/poisson.md)), Monte Carlo generates the full probability distribution over every possible scoreline directly by simulation. This lets you:

- Identify mispriced specific scores
- Price "winning margin" markets (win by exactly 1, by 2+, etc.)
- Compute the probability of any score range or subset

### 3. Season Simulations and Futures

Futures markets price outcomes like "which team wins the division?" or "will this team make the playoffs?" Simulating a full season:

1. Assign win probabilities to each remaining game using your model
2. Simulate every remaining game using those probabilities
3. Record the outcome (standings, playoff seedings)
4. Repeat 10,000–50,000 times
5. Count the frequency of each outcome

The resulting distribution can be compared against bookmaker futures odds to identify value. This approach accounts for schedule difficulty, head-to-head records, and the cascading effect of early-season results.

### 4. Parlays and Correlated Bets

Standard parlay pricing assumes legs are independent. In practice, legs from the same game are correlated (if a team scores many points, both the moneyline and the over are more likely to hit). Monte Carlo handles this correctly by simulating game states jointly and evaluating all parlay legs simultaneously.

This is also how same-game parlay (SGP) fair values are computed — by simulating the full game state and counting how often all legs hit simultaneously.

### 5. Bankroll Growth and Risk of Ruin

Monte Carlo is the standard tool for simulating long-run bankroll trajectories and estimating ruin probability:

1. Define a strategy (edge per bet, bet sizing rule, bet frequency)
2. Simulate a sequence of bet outcomes using the win probability distribution
3. Track bankroll over time
4. Repeat 10,000+ times
5. Estimate: probability of ruin, expected bankroll after N bets, 5th/95th percentile trajectories

This gives a realistic picture of the range of outcomes rather than just expected value, helping set proper expectations and bankroll buffers. See [`bankroll-management.md`](../strategy/bankroll-management.md) for context on how these simulations inform bet sizing.

## Accuracy and Convergence

Monte Carlo estimates converge at a rate of `1/√N`. Standard error:

```
SE = √(p × (1-p) / N)
```

For `p = 0.5` (worst case), 10,000 simulations gives SE ≈ 0.5%. For most betting applications, this is more than adequate.

Practical simulation counts:
- Single-game outcome distribution: 10,000 simulations
- Season simulation: 10,000–50,000 simulations
- Bankroll ruin estimation: 10,000–100,000 paths
- Correct-score market pricing: 100,000+ simulations for low-probability scorelines

## Variance Reduction Techniques

For computationally expensive simulations, these techniques reduce the number of required simulations for a given accuracy level:

**Antithetic variates**: for each random draw, also simulate its mirror image. Reduces variance by introducing negative correlation between pairs of simulations.

**Control variates**: subtract a correction term based on a quantity with known expectation (e.g., the mean of a simple approximation). Reduces the effective variance of the estimator.

**Importance sampling**: sample more heavily from the tail of the distribution (rare events) and reweight the results. Useful when estimating low-probability outcomes like parlays.

For most sports betting applications, these are not necessary — brute-force simulation is fast enough.

## Implementation Notes

- Use a vectorized implementation (NumPy, Go slices with goroutines) rather than a Python loop for large simulation counts
- Seed the random number generator for reproducibility during development; use different seeds in production
- Pre-compute any static distributions (e.g., Poisson parameters) before the simulation loop
- For season simulations, simulate each remaining game in schedule order and update standings sequentially within each trial

## Limitations

**Garbage in, garbage out**: Monte Carlo estimates are only as good as the underlying model assumptions. If the input probability distribution is miscalibrated, the simulation will produce confidently wrong estimates. See [`calibration.md`](calibration.md).

**Independence assumptions**: many simulations assume game outcomes are independent. In reality, outcomes are correlated through factors like team momentum, weather patterns, or referee assignments. Ignoring correlation understates tail risk in season simulations.

**Computational cost**: season simulations across a full league with 10,000 trials and 30+ teams × 162 games each can take significant compute time if not vectorized.
