# Data and Features

Feature engineering — selecting and constructing the right inputs for your model — has been consistently identified in sports betting research as more important than the choice of algorithm. A simple logistic regression with excellent features will outperform a complex neural network with poorly chosen ones. This document covers data sources, the types of features that matter, and practical considerations for building a reliable feature pipeline.

## Data Sources

### Historical Game Results

The foundation of any model. At minimum, you need final scores and game metadata (date, teams, venue, season). Sources:

- **Sports-reference.com** (free): comprehensive historical results for major American sports (NFL, NBA, MLB, NHL, college football/basketball)
- **API-sports.io**: REST API for dozens of sports including soccer leagues worldwide
- **ESPN/Rottentomatoes APIs** (unofficial): public endpoints for results and schedules
- **Rapid API sports endpoints**: aggregates multiple sports data providers

### Historical Odds Data

Critical for backtesting — you need the odds that were actually available at bet time, not just game results.

- **Odds Portal**: free historical odds for many sports and leagues
- **The Odds API**: subscription service with historical and live odds across multiple bookmakers
- **Pinnacle historical data**: Pinnacle's lines are widely considered the most efficient and are used as a benchmark by serious bettors
- **Betfair Exchange data**: exchange markets provide a market-clearing price without bookmaker margin — useful for estimating true probabilities

### Advanced Metrics / Tracking Data

Beyond box scores, advanced metrics capture the "how" behind results:

- **Expected Goals (xG)** (soccer): how dangerous were the shots taken? Available from Understat, FBref, StatsBomb (premium)
- **FBref / StatsBomb** (soccer): player-level passing networks, progressive carries, defensive actions
- **NBA tracking**: Second Spectrum provides player/ball tracking for all NBA games; aggregated metrics available on Cleaning the Glass and PBP Stats
- **NFL Next Gen Stats**: player tracking data published by the NFL; passer pressure rates, route running, separation
- **Baseball Savant**: Statcast data for all MLB games — exit velocity, launch angle, sprint speed, spin rate

### Betting Market Data

Sometimes the market's own movement is an informative feature:

- Opening vs. closing line differential
- Public betting percentages (available from The Action Network, Bet Labs)
- Sharp money indicators (money percentages vs. ticket percentages)

Use this data carefully — incorporating it as a training feature risks introducing circular logic if your model is trying to improve on the market. See [`market-efficiency.md`](../foundations/market-efficiency.md).

### External Contextual Data

- **Weather**: weather conditions (wind speed, temperature, precipitation) are predictive for outdoor sports, particularly NFL and baseball. OpenWeatherMap and Weather API provide historical and forecast data.
- **Rest and travel**: days since last game, distance traveled, time zone changes — all have empirical support as predictive features
- **Referee assignments**: in soccer particularly, individual referee characteristics (cards per game, home-win rates) are predictive

---

## Feature Categories

### Team Strength Indicators

Measures of overall team quality that provide a prior before game-specific information is applied:

- **Elo ratings**: dynamic strength estimates updated after each game. See [`models/elo.md`](models/elo.md)
- **Points per game** (adjusted for opponent quality)
- **Point differential** (actual margin of victory)
- **Expected goals differential** (soccer): better predictor of future performance than actual goals
- **Power ratings**: composite measures published by analytics providers (e.g., FPI, BPI, SRS)

### Recent Form

How a team has been performing in the last N games:

- Rolling win rate (last 5, 10 games)
- Rolling point differential
- Rolling xG differential (soccer)
- Streak length (current winning or losing streak)

**Important**: use rolling windows carefully. If Team A played all their recent games against weak opponents, their recent form metrics are misleading. Always consider opponent-adjusted figures.

### Head-to-Head History

Historical results between specific matchups. Useful in some sports (tennis, soccer rivalries) but often overfitted — especially in sports with high roster turnover, head-to-head history from three years ago says little about today's matchup.

### Situational Factors

Contextual circumstances that affect performance:

- **Home/away**: home advantage is real and quantifiable. The size varies by sport (larger in soccer, smaller in NBA, nearly nonexistent in MLB)
- **Rest**: back-to-back games in NBA and NHL significantly affect performance
- **Travel**: teams traveling across multiple time zones show measurable performance decrements
- **Motivation/stakes**: elimination games, rivalry matchups, meaningless late-season games all affect effort level

### Injury and Roster

The most impactful but most difficult data to systematize:

- Player availability and expected minutes
- Injury recovery status (game-time decisions vs. confirmed out)
- Quality of injured player (an injured backup matters less than an injured starter)

**Challenge**: injury information often becomes available shortly before game time and causes rapid line movement. Models that incorporate injury data must be re-run whenever new injury reports are released.

### Pace and Scoring Environment

Especially important for totals markets:

- **Pace**: possessions per game (basketball), average time between scoring events
- **Offensive and defensive ratings**: points scored/allowed per possession or per game
- **Environmental factors**: dome vs. outdoor, altitude, turf vs. grass

---

## Feature Engineering Principles

### Avoid Lookahead Bias

Every feature must be computable using only data available before the game being predicted. A season average computed at season end is not available in week 3. Always compute features as rolling or trailing windows anchored to the prediction date. See [`backtesting.md`](backtesting.md).

### Opponent Adjustment

Raw statistics (points per game, shooting percentage) mix together the team's quality and their opponents' quality. Opponent-adjusted metrics — comparing a team's performance against opponent-expected performance — are almost always more predictive than unadjusted stats.

Example: a team allowing 110 points per game against an average opponent is playing better defense than a team allowing 108 points per game against weak opponents all season.

### Stationarity and Recency Weighting

Sports statistics are non-stationary — team quality changes over the course of a season due to trades, injuries, development, and coaching adjustments. Features computed over longer historical windows may include data from a team that no longer exists in its current form.

Common approaches:
- Use only the last N games (rolling window)
- Apply exponential decay weighting (recent games count more than older ones)
- Use Elo-style updates that inherently downweight old information

### Feature Importance vs. Feature Complexity

Research consistently finds diminishing returns from adding more features. Start with the highest-signal features (team strength difference, home/away, rest differential) and add more only when they demonstrably improve out-of-sample calibration. A model with five well-chosen features often beats one with fifty poorly chosen ones.

---

## Pipeline Considerations

### Data Freshness

For live deployment, the feature pipeline must update as new information arrives:
- Injury reports (typically released the day before and morning of a game)
- Weather forecasts (update every few hours)
- Line movements (continuous)

Stale features mean stale predictions. Build the pipeline to pull fresh data on each prediction run.

### Data Quality and Consistency

Sports data providers have inconsistent team and player name conventions. A player named "Jared Goff" in one dataset may be "J. Goff" in another. Build normalization layers (canonical player and team IDs) early.

Missing data is common: a player with no recorded minutes in a game may be injured, suspended, or simply not tracked. Missing values need explicit handling — do not silently propagate NaN through calculations.

### Feature Versioning

When you update a feature definition (e.g., changing a rolling window from 10 games to 7 games), old backtests are no longer comparable to new ones. Track feature definitions alongside model versions.
