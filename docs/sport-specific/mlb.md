# MLB Betting Guide

Major League Baseball has more games than any other major North American sport — 2,430 regular-season games across 30 teams. This volume is both an opportunity (large sample sizes) and a challenge (high variance per game). Baseball is the most pitcher-dominated sport for betting purposes: the starting pitcher matchup is the single most important variable in any individual game prediction.

## Market Structure

The MLB regular season runs April through September. Each team plays 162 games. Total betting volume:
- A single-sport MLB bettor placing one bet per game can accumulate 500–800 bets per season — enough for meaningful statistical conclusions in one or two seasons
- See [`variance-and-sample-size.md`](../foundations/variance-and-sample-size.md)

### Bet Types

- **Moneyline**: by far the most common MLB bet; no spread (just win/loss)
- **Run line**: MLB's version of a spread; almost always set at ±1.5 runs. Favorites at -1.5, underdogs at +1.5
- **Totals**: typically set between 7.5 and 9.5 runs for most games
- **First 5 innings (F5)**: bets resolved at the end of 5 innings, removing bullpen variance — allows pure starting-pitcher matchup bets
- **Player props**: pitcher strikeouts, batting stats (see [`prop-betting.md`](../strategy/prop-betting.md))

### Action vs. Listed Pitcher Rules

Most sportsbooks offer two types of listings:
- **Listed pitcher (action only if named pitcher starts)**: the bet is voided if the listed starting pitcher does not start. This is the preferred option for pitcher-specific models.
- **Action**: the bet stands regardless of who starts. Avoid this for games where starting pitcher identity is uncertain.

Always bet "listed pitcher" or verify the starter before placing any MLB bet.

---

## The Starting Pitcher Dominance

No other major sport has a single player position this determinative of a game's outcome. A team's expected runs allowed is primarily a function of the starting pitcher — not the fielders behind them (within reasonable ranges) and not the bullpen for the first 5–6 innings.

### Pitcher Quality Metrics

**ERA (Earned Run Average)**: traditional metric, heavily influenced by luck (unearned runs excluded, BABIP variance included). Useful for historical context but not for prediction.

**FIP (Fielding-Independent Pitching)**: models expected ERA based only on outcomes the pitcher controls — strikeouts, walks, hit batters, home runs. Formula:

```
FIP = (13×HR + 3×(BB + HBP) - 2×K) / IP + FIP_constant
```

The constant (≈ 3.10 historically) normalizes FIP to ERA scale. FIP is a better predictor of future ERA than past ERA.

**xFIP (Expected FIP)**: like FIP but replaces actual home runs with an expected home run rate (using fly ball rate × league-average HR/FB ratio). Reduces park-factor noise and is more stable.

**SIERA (Skill-Interactive ERA)**: the most sophisticated publicly available metric; accounts for the interaction between strikeout rate, walk rate, and ground ball rate. Available from FanGraphs.

**For betting models**: use xFIP or SIERA as your primary pitcher quality input, not ERA or even FIP.

### Stuff Metrics

Statcast provides pitch-level tracking data that enables "stuff" metrics — how good is each pitch independent of results:

- **Velocity trends**: decreasing velocity often precedes performance decline
- **Spin rate**: affects pitch movement; higher spin generally means more effective breaking balls
- **Whiff rate**: swings and misses per swing — direct measure of swing-and-miss stuff
- **Hard hit rate allowed**: percentage of balls hit above 95 mph exit velocity

These are available from Baseball Savant (free) and give real-time data on pitcher effectiveness beyond ERA.

---

## Bullpen

For full-game bets, bullpen quality matters significantly once the starter exits (typically inning 5–7). For F5 bets, it is irrelevant.

### Bullpen Metrics

- **Leverage Index**: measures the importance of each plate appearance; high-leverage situations are where closer/setup quality matters
- **Bullpen ERA / FIP**: aggregate quality of relief pitchers
- **Recent usage**: a bullpen that has been heavily used in the past 3 days is degraded relative to a rested bullpen

**Fatigue signal**: if the bullpen has thrown 30+ innings in the last 5 days, expect degraded performance. This is especially relevant in playoff scenarios. See [`tournament-and-playoff-modeling.md`](../strategy/tournament-and-playoff-modeling.md).

---

## Park Factors

Baseball parks vary dramatically in dimensions, altitude, and atmospheric conditions. A home run in Denver (Coors Field) would be a long fly out in Petco Park (San Diego). Park factors normalize team and player statistics for the environment.

### Run-Scoring Park Factors

Available from Baseball Reference and FanGraphs. A park factor of 110 means the park produces 10% more runs than average. Key outliers:

| Park | Factor | Direction |
|------|--------|-----------|
| Coors Field (COL) | ~120 | Extreme hitter's park (altitude) |
| Fenway Park (BOS) | ~105 | Hitter-friendly (Green Monster) |
| Petco Park (SD) | ~95 | Pitcher-friendly |
| Oracle Park (SF) | ~94 | Pitcher-friendly (cold, marine air) |
| Yankee Stadium | ~108 | Right-field porch favors lefty power |

Always apply park factor adjustments before comparing team statistics. A team with a 4.50 ERA at Coors Field may have a 3.80 "true" ERA.

### Weather Interaction with Parks

See [`weather-modeling.md`](../modeling/weather-modeling.md). Wind direction relative to outfield orientation and temperature interact with park dimensions. A wind-out day at Fenway is materially different from a wind-in day at Coors.

---

## Platoon Splits

Most batters perform differently against left-handed vs. right-handed pitchers. Right-handed batters typically hit better against left-handed pitchers (opposite hand advantage), and vice versa.

**Left-handed starter advantage/disadvantage**: starting a left-handed pitcher against a lineup heavy with left-handed batters creates a measurable disadvantage for the starting team. This is a routine adjustment in professional baseball modeling.

**Data source**: Baseball Reference provides career and season platoon splits for all pitchers and batters.

---

## Run Line Modeling

The run line (±1.5 runs) creates a different betting calculation than the moneyline.

**Intuition**: betting the favorite at -1.5 means they must win by 2+. Approximately 60–65% of games won by the favorite are won by 2+ runs (i.e., roughly 40% of favorite wins are by exactly 1 run, which loses the run line). Conversely, betting the underdog at +1.5 wins if they win outright OR lose by exactly 1 run.

**When run line edges arise**:
- When the moneyline is very short (-150 to -170) but the run line is priced at +100 to -105: the value of the 1.5-run cushion may outweigh the cost
- This can be evaluated using the full run distribution from your Poisson or normal distribution model

---

## Home-Field Advantage

Historical MLB home-field advantage: approximately 0.25–0.30 runs per game (teams win ~54% of home games). This is smaller than NFL or NBA. The effect is primarily driven by:
- Familiarity with the batter's eye and background
- Scheduling (home teams avoid cross-country travel)
- Fan support in high-leverage situations (modest)

### Travel Effects

MLB has the most travel of any major sport. A team finishing a west coast road trip and immediately beginning a home series may show residual fatigue. The west-to-east travel on short rest is the most impactful trip type.

---

## Modeling Approach

### Recommended Feature Set

| Feature | Notes |
|---------|-------|
| Starting pitcher xFIP / SIERA | Primary quality signal |
| Bullpen xFIP last 7 days | Full-game bets only; exclude for F5 |
| Bullpen innings thrown last 5 days | Fatigue proxy |
| Park factor (run-scoring) | Apply to both teams |
| Weather: wind direction/speed | Ball carry effect |
| Weather: temperature | Run-scoring impact |
| Platoon advantage | Lineup vs. starter handedness |
| Home/away | ~0.25–0.30 run advantage |
| Team wRC+ (last 15 games) | Offensive form, weighted by recency |
| Team defensive efficiency | DRS, OAA (Outs Above Average) |

---

## Resources

- **Baseball Savant** (baseballsavant.mlb.com): Statcast data — exit velocity, launch angle, spin rate, xFIP; free
- **FanGraphs** (fangraphs.com): FIP, xFIP, SIERA, WAR, park factors; mostly free
- **Baseball Reference** (baseball-reference.com): historical box scores, splits, league history; free
- **Retrosheet**: play-by-play data going back to the 1950s; free
- **Baseball Prospectus**: PECOTA projections, DRC+ (offense), DRA (pitching); subscription
