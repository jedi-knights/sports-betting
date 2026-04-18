# Tournament and Playoff Modeling

Playoff and tournament betting presents a structurally different challenge from regular-season modeling. Samples are tiny, home-field advantage changes, rest dynamics are unusual, and team motivation is at its peak for all participants. Models trained on regular-season data do not transfer directly without meaningful adjustments.

## Why Playoffs Are Different

### Sample Size Collapse

An NFL team plays 17 regular-season games but only 1–4 playoff games. An NBA team plays 82 regular-season games but may face the same opponent 7 times in a single series. The data available to calibrate playoff-specific performance is orders of magnitude smaller than regular season.

This forces greater reliance on underlying skill metrics (Elo ratings, efficiency differentials) rather than recent results, and requires wider uncertainty intervals on all predictions.

### Roster and Effort Selection

Playoff teams have typically been managing injuries, rest, and lineup rotation throughout the regular season. In the playoffs:
- Injured players often push through that would have sat in regular-season games
- Coaches abandon regular-season rotation strategies and play their best lineups maximum minutes
- Load management (common in NBA regular season) disappears entirely

This means regular-season per-minute metrics, when properly scaled, may actually be more predictive of playoff performance than raw regular-season production.

### Coaching Adjustments

Elite coaches — and their opponents know this — make significant in-series adjustments that can render early-series game data irrelevant by Game 5. Statistical trends observed in Games 1–2 of an NBA series may be deliberately designed to set up Games 3–4 exploits.

This makes within-series pattern recognition dangerous. The market adjusts quickly; a line that moves based on Game 2 trends may already fully price in the adjustment.

### Motivation and Focus

All teams remaining in a playoff are, by selection, motivated. The motivation differential that drives some regular-season edges (a team with nothing to play for vs. a team fighting for seeding) does not apply in playoffs. This removes one useful modeling feature entirely.

---

## Home-Field Advantage in Playoffs

Home-field advantage exists in playoffs but differs in magnitude and structure from the regular season.

### NFL Playoffs

Regular-season home advantage in NFL: approximately 2.5–3 points. In the playoffs, this estimate is similar but with much wider confidence intervals due to small sample sizes. The Super Bowl is played at a neutral site and carries no home-field advantage.

Factors that modify home-field value:
- **Temperature and weather**: cold-weather home teams (Green Bay, Buffalo) may benefit more from playing at home in January than warm-weather teams
- **Travel disadvantage**: a cross-country road trip in January for a warm-weather team playing at a cold venue is a compounding disadvantage

### NBA Playoffs

Regular-season home advantage in NBA: approximately 3.5 points (teams win roughly 60% of home games). In the playoffs, this number is slightly lower — approximately 3 points. The playoff crowd is more intense, but the road team is also better (only top teams are in the playoffs) and more acclimated to hostile road environments.

**Series home-field structure**: in a 2-2-1-1-1 series (standard NBA), having home-court advantage means Games 1, 2, 5, and 7 at home (if it goes that far). The probability of winning the series given home-court advantage is approximately 65% historically.

### MLB Playoffs

Home-field advantage in MLB is smaller than in the other major sports (empirically ~55% home win rate). This reflects the high variance of individual games in baseball (great starting pitchers largely determine individual game outcomes regardless of venue).

### NCAA Tournament (March Madness)

All games are played at neutral sites after the first weekend. True neutral-site adjustments should apply. The first two rounds often feature "protected" home regions where one team plays within driving distance — this acts as a partial home-field advantage and is worth modeling.

---

## Series Modeling (NBA, MLB Playoffs)

Playoffs in the NBA and MLB are structured as best-of-seven series. Series win probability is not the same as individual game win probability.

### From Game Probability to Series Probability

If Team A has a constant probability `p` of winning each game (independent games):

```
P(series win in 4) = p⁴
P(series win in 5) = C(4,3) × p³ × (1-p) × p = 4p⁴(1-p)
P(series win in 6) = C(5,4) × p⁴ × (1-p)² × p
P(series win in 7) = C(6,5) × p⁵ × (1-p)² × p × ... (full expansion)
```

Total series win probability:

```python
from math import comb

def series_win_prob(p, games_required=4, series_length=7):
    total = 0
    for wins in range(games_required, series_length + 1):
        losses = wins - 1  # must win the final game
        # Choose which games are losses (not the last game, which is a win)
        total += comb(wins - 1, losses) * (p ** wins) * ((1 - p) ** losses)
    return total
```

For `p = 0.55`: series win probability ≈ 60.8%.
For `p = 0.60`: series win probability ≈ 71.0%.

The gap between per-game edge and series edge highlights why series betting at favorable prices can be very valuable.

### Home-Court-Adjusted Series Model

If home team wins with probability `p_home` and road team wins with probability `p_away = 1 - p_home` (where `p_home > p_away` due to home-court advantage), then you need to simulate each game in sequence based on location:

```
Game 1: home team home → use p_home
Game 2: home team home → use p_home
Game 3: away team home → use 1 - p_home
...
```

This is most naturally handled with Monte Carlo simulation (see [`monte-carlo.md`](../modeling/monte-carlo.md)) rather than the analytical formula, since the formula assumes constant per-game probability.

### In-Series Adjustment

Per-game win probability should update between series games based on:
- Observed performance (efficiency differentials in the series itself)
- Injury developments within the series
- Coaching adjustments that appear to have structural effects

Weight in-series data carefully — 1–2 games is not statistically meaningful, but a consistent 4-game pattern of one team dominating in a specific area should receive some weight.

---

## Tournament Bracket Modeling

For NCAA March Madness, NFL playoffs, World Cup, and similar structures, the goal is to assign probability estimates to each team reaching each stage of the bracket.

### Bracket Simulation

1. Assign each team a strength rating (Elo, KenPom for NCAA, FPI for NFL)
2. For each potential matchup, compute win probability from strength ratings
3. Simulate the full bracket 10,000–100,000 times using Monte Carlo
4. Count how often each team reaches each round

This produces a full probability matrix: each team × each possible finish.

### Comparing Against Futures Market

With the simulation results in hand, compare each team's probability of winning the championship (or reaching a specific round) against the implied probability from futures odds.

```
value = model_probability - market_implied_probability
```

Teams with significantly higher model probability than market probability at positive odds are value futures bets.

### Path Dependency

A team's path through the bracket matters as much as their raw strength. A strong team on the "easy side" of the bracket has a higher probability of reaching the final than the same team on the "hard side." Models must account for the full path probability, not just per-game matchup probability.

This is why bracket simulation (rather than simple win probability calculation) is the right tool — it captures path dependency automatically.

---

## Practical Adjustments for Playoff Models

### Upweight Efficiency Metrics Over Raw Results

In the playoffs, a team that won ugly (close games, luck-dependent outcomes) in the regular season may revert toward their underlying efficiency metrics. Use:
- NBA: offensive/defensive rating per 100 possessions
- NFL: DVOA, EPA (expected points added)
- MLB: xFIP (expected fielding-independent pitching), team xwOBA
- Soccer: xG differential

These metrics regress toward true talent faster than raw win-loss records.

### Increase Uncertainty Intervals

Given the smaller sample sizes and higher variance of playoff environments, widen your confidence intervals relative to regular-season estimates. A team whose regular-season model gives 65% probability should perhaps be estimated at 60% for playoff games due to increased uncertainty.

### Matchup-Specific Adjustments

Playoff opponents are known in advance. Adjust for:
- Stylistic mismatches (a team that struggles against zone defense; an opponent that runs zone)
- Pitching matchup rotations (MLB)
- Historical head-to-head in playoff contexts (small sample, use cautiously)
