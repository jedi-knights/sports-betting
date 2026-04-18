# Soccer Betting Guide

Soccer (association football) is the world's most bet sport by volume. It offers thousands of league markets across every continent, a third outcome (the draw), and a rich ecosystem of advanced data. The Poisson model was developed specifically for soccer goal-scoring, and the sport has the deepest publicly available research literature of any sport in this repository.

## Market Structure

Unlike American sports, soccer betting happens across hundreds of leagues worldwide:

- **Top leagues** (Premier League, La Liga, Bundesliga, Serie A, Ligue 1): highly efficient, heavy sharp action
- **Second-tier leagues** (Championship, Serie B, MLS, Eredivisie): moderate efficiency
- **Lower leagues**: less efficient, higher potential edge but worse data quality

The number of games available far exceeds any single American sport. A bettor focused on European leagues alone can access 5,000+ games per season.

### Bet Types

- **1X2 (Match Result)**: home win (1), draw (X), away win (2). The foundational soccer market.
- **Asian Handicap**: fractional point spreads that eliminate the possibility of a push. More liquid than 1X2 in many international markets.
- **Double chance**: bet on two of three outcomes simultaneously (1X, X2, 12). Higher implied probability, lower odds.
- **Both Teams to Score (BTTS)**: will both teams score at least one goal?
- **Over/Under goals**: typically 2.5 total goals is the standard line
- **Correct Score**: exact final score; high-margin market, but Poisson models can identify value
- **Anytime Scorer**: will a specific player score at any point in the game?

---

## The Draw: Soccer's Third Outcome

The draw is the defining structural difference between soccer and American sports betting. In the Premier League, approximately:
- 46% of games are home wins
- 27% are draws
- 27% are away wins

A Poisson model (see [`models/poisson.md`](../modeling/models/poisson.md)) naturally produces a draw probability alongside home and away win probabilities. Modeling draws well is crucial — they are where the most profit is available since bookmakers often price them less precisely than the two win outcomes.

### Draw Tendencies

Some teams and matchups have higher draw rates due to tactical styles:
- Defensive-minded teams deploy low blocks and counterattack, producing lower-scoring games and more draws
- Top clubs playing lower opposition often see the lower side defend with 10 men, also increasing draw probability
- Rivalry games and cup competitions can see increased defensive caution

---

## Expected Goals (xG)

Expected goals is the most important advanced metric in soccer modeling. It estimates the probability of a goal from each shot based on:
- Shot location (distance and angle from goal)
- Shot type (header, right foot, left foot)
- Assist type (whether preceded by a through ball, cross, etc.)
- Game state (open play vs. set piece)

**Why xG is more predictive than actual goals**: teams that consistently score goals without accumulating high xG are benefiting from shooting luck (high conversion rates above expectation) that tends to regress. Teams with high xG but low goals scored are likely to "catch up." xG differential is the strongest available predictor of future points in the league table.

### xG Data Sources

- **Understat** (understat.com): xG for all shots in the top 5 European leagues; free
- **FBref / StatsBomb**: team and player xG, progressive passes, defensive actions; free for public data
- **Opta / StatsBomb (premium)**: the most detailed shot models; commercial access
- **WhoScored**: publicly available metrics including some shot quality data

---

## League Selection

Not all leagues are equally modelable. Key considerations:

### Data Quality

Top leagues (Premier League, Bundesliga, La Liga) have:
- Detailed Opta or StatsBomb data going back 10+ years
- xG models trained on large sample sizes
- Multiple publicly available advanced metrics

Lower leagues may have:
- Only box scores (goals, shots, cards)
- No xG data
- Inconsistent team identity (promotion/relegation means rosters change dramatically year to year)

### Market Efficiency

Top leagues are priced efficiently by sharp bookmakers (Pinnacle, SBO). Lower leagues have:
- Less sharp action monitoring the market
- Bookmakers using simpler models
- More potential for edge — but also more risk from data quality issues

### Recommendation for Beginners

Start with one top-tier league (Premier League or Bundesliga) where:
- Data quality is high
- Modeling research is most developed
- Historical odds are widely available for backtesting

After establishing a working model, consider expanding to second-tier leagues where efficiency is lower.

---

## Home-Field Advantage by League

Home-field advantage varies significantly across leagues:

| League | Approx. home win rate | Notes |
|--------|----------------------|-------|
| Premier League | 45–46% | Near-average; large stadiums, mixed atmospheres |
| Bundesliga | 46–47% | Slightly above average |
| Serie A | 44–45% | Average |
| La Liga | 46–47% | Slightly above average |
| MLS | 49–50% | Higher; travel distances are large in North America |
| Championship (English second tier) | 46–47% | Similar to top flight |
| Lower leagues generally | 48–52% | Higher; more loyal local fan bases, less travel acclimatization |

Model home-field advantage separately by league and update annually — home advantage has declined in most European leagues since 2020 (COVID-era empty stadium effect is now mostly washed out).

---

## Asian Handicap Markets

Asian Handicap is widely used in Asian markets and increasingly available globally. It works similarly to American point spreads but with fractional handicaps that eliminate draws:

- **Half-goal handicaps** (-0.5, +0.5, -1.5, +1.5): no push possible
- **Quarter-goal handicaps** (-0.25, +0.25): the bet is split between two adjacent half-handicaps
- **Whole-goal handicaps** (-1, +1, -2): push is possible (bet refunded) if the margin equals the handicap

**Why Asian Handicap?**
- Lower bookmaker margin than 1X2 markets (often 2–3% vs. 4–6%)
- Removes the draw outcome complexity from the prediction problem
- More liquid in many Asian-facing bookmakers

For a Poisson model: convert the goal distribution into Asian Handicap probabilities by computing the probability that the margin exceeds or falls short of each handicap value.

---

## Building a Soccer Model

### The Poisson Framework

The Poisson model described in [`models/poisson.md`](../modeling/models/poisson.md) is the foundational approach. The implementation steps for a league model:

1. Collect historical results (at minimum 3 seasons; 5+ is better)
2. Estimate attack and defense strength parameters for each team using maximum likelihood
3. Apply time-decay weighting to emphasize recent matches
4. Compute expected goals `λ_home` and `λ_away` for each fixture
5. Apply Dixon-Coles correction for low-scoring outcomes
6. Derive 1X2 probabilities, correct-score probabilities, and over/under probabilities from the scoreline matrix

### Model Inputs Beyond Attack/Defense Ratings

More sophisticated models incorporate:
- **xG-based ratings**: use xG data instead of (or alongside) actual goals for attack/defense parameters — produces more stable estimates
- **Recent form**: apply stronger time-decay in periods of rapid team change (new manager, January transfers)
- **Head-to-head**: useful only in domestic cups where the same teams meet repeatedly; less useful in league play
- **Squad depth and rotation**: managers rest players for cup games or in congested fixture lists
- **Injury and suspension**: key player absences that alter the effective team rating

---

## Resources

- **Understat** (understat.com): xG for top 5 European leagues; free
- **FBref** (fbref.com): comprehensive stats powered by StatsBomb data; free
- **Transfermarkt**: transfer history, squad market values, player profiles; free
- **Football-data.co.uk**: historical match results and odds for dozens of leagues going back to 1993; free — essential for backtesting
- **Opta / StatsBomb (commercial)**: professional data; required for elite modeling
- **SoccerWay / SofaScore**: results, lineups, and stats for hundreds of leagues; free
