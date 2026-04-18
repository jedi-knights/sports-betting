# NFL Betting Guide

The NFL is the most heavily bet sport in the United States and one of the most efficiently priced markets in the world. Game lines on major NFL matchups incorporate enormous amounts of sharp action within hours of opening. This makes it a challenging market for model-based edge — but also a deeply researched one with extensive historical data and well-understood structural characteristics.

## Market Structure

The NFL season runs approximately September through January (17 regular-season weeks plus playoffs). This means roughly:

- 272 regular-season games per season
- 13–14 playoff games
- 1 Super Bowl

At typical betting frequencies, a single-sport NFL bettor may place 200–400 bets per season across spreads, totals, and moneylines. See [`variance-and-sample-size.md`](../variance-and-sample-size.md) for why multiple seasons are needed before drawing conclusions.

### Most Liquid Markets

- **Point spreads**: most efficient, highest volume
- **Totals (over/under)**: efficient, well-studied
- **Moneylines**: less efficient on large underdogs due to parlay demand inflating underdog odds
- **Player props**: higher margin, less sharp action — better edge opportunities for modelers

---

## Key Numbers

The most important structural feature of NFL betting is the distribution of game margins. Because of the scoring system (touchdowns = 7, field goals = 3), certain margins of victory are far more common than others.

| Margin | Frequency (approx.) |
|--------|---------------------|
| 3 | ~15% of games |
| 7 | ~9% |
| 10 | ~6% |
| 6 | ~6% |
| 4 | ~5% |

The most important key numbers are **3** and **7**. A spread at exactly 3.0 is worth significantly more than 3.5 — the difference between a push and a loss. Paying an extra half-point to buy from 3.5 to 3 or 7.5 to 7 (teaser-style) is almost always worth the vig cost.

### Practical Implication

When shopping lines (see [`line-shopping-and-account-management.md`](../line-shopping-and-account-management.md)):
- Getting Team A -2.5 vs. -3.5 is a significant difference — a 3-point final margin is roughly a 15% probability event
- Getting Team B +3.5 vs. +3.0 is equally important in the other direction
- Lines at -3 and -7 tend to be stickier — books hold these numbers longer because the public knows their value

---

## Weather Effects

Weather has the most measurable impact on NFL totals of any major North American sport. See [`weather-modeling.md`](../weather-modeling.md) for full detail. Summary:

- **Wind > 20 mph**: reduce expected total by 3–5 points; bet unders
- **Precipitation**: modest negative impact on scoring; modest positive impact on rushing
- **Cold < 32°F**: small negative impact on scoring; larger impact on teams unaccustomed to cold
- **Dome games**: no weather effect; do not apply weather features to these matchups

Weather data should be incorporated as a model feature and also monitored for late line adjustments — if weather worsens significantly in the 24 hours before a game, the total line often moves but not always fully.

---

## Injury Timing and Information

NFL injury reports are a structural feature of the market. The league mandates injury designations:

- **Out**: will not play
- **Doubtful**: ~25% chance of playing
- **Questionable**: ~50% chance of playing
- **Probable**: ~75% chance of playing (rarely used now)
- **DNP / Limited / Full participation** in practice reports

The Wednesday/Thursday/Friday practice reports reveal injury progression. The most valuable information window is **Friday–Saturday**, when final designations before Sunday games are released.

A starting quarterback listed as "doubtful" who becomes "out" on Friday typically moves the line 5–7 points. Modeling the value of this transition before the market fully adjusts requires:
1. A "with starter" and "without starter" model probability estimate
2. A fast news-monitoring pipeline to detect designation changes before the market moves

### Betting on Injury News

This is one of the most consistent edge sources in NFL: betting immediately after an injury designation changes but before the line fully adjusts. This requires infrastructure — automated news parsing or a reliable alert service — and fast execution.

---

## Home-Field Advantage

Historical NFL home-field advantage: approximately 2.5–3 points. This has declined slightly over the past decade, possibly due to:
- Increased travel infrastructure
- Reduced crowd noise effect in recent stadium designs
- More neutral fan attendance at premium games

**Adjustments**:
- **Divisional games**: home-field advantage is slightly reduced because teams are familiar with each other's home venues and travel routinely
- **Cold-weather home teams in January**: Green Bay, Buffalo, and similar teams may have above-average home advantage in playoff months against warm-weather opponents
- **Neutral-site Super Bowl**: no home-field adjustment

---

## Rest and Schedule

### Bye Weeks

Teams coming off a bye week have had two weeks to prepare and rest. Historical performance off the bye is slightly positive (~1 point better against the spread than expected). This is a well-known market factor and may already be priced in efficiently, but is worth testing as a model feature.

### Short-Week Games (Thursday Night)

Teams playing on Thursday after a Sunday game have had only 3 days of rest and preparation. This is a consistent negative factor, especially for:
- Teams traveling cross-country
- Teams with a significant number of injured players recovering

### Divisional Schedule Patterns

In the second half of the season, teams often play multiple divisional games in a row. Divisional games historically see slightly lower scoring and tighter results — teams are familiar with each other's systems and personnel.

---

## Modeling Approaches

### Team Strength Metrics

- **DVOA (Defense-adjusted Value Over Average)**: Football Outsiders' signature metric. Measures efficiency relative to league average, adjusted for opponent quality. One of the most predictive publicly available NFL metrics.
- **EPA (Expected Points Added) per play**: increasingly used as a real-time efficiency metric. Available from nflfastR (free, play-by-play data)
- **Elo ratings**: See [`models/elo.md`](../models/elo.md) — effective for relative strength but less granular than EPA-based metrics

### Recommended Feature Set (Starting Point)

| Feature | Why it matters |
|---------|---------------|
| DVOA differential | Opponent-adjusted efficiency signal |
| Elo rating difference | Simple relative strength baseline |
| Home/away indicator | 2.5–3 point structural adjustment |
| Rest differential (days since last game) | Back-to-back disadvantage, bye week advantage |
| Travel distance | Cross-country trips are measurably worse |
| Wind speed at game time | Totals adjustment |
| Precipitation binary | Totals and rushing vs. passing split |
| Divisional game indicator | Tighter lines, lower scoring historically |
| QB health indicator | Most impactful individual player in sport |

---

## Resources

- **nflfastR** (R package / Python port): play-by-play data for all NFL games since 1999; EPA, success rate, and other derived metrics
- **Football Outsiders**: DVOA, DYAR, and team rankings going back two decades
- **Pro Football Reference**: box scores, splits, historical game logs
- **NFL Next Gen Stats**: official league tracking data (public aggregates)
