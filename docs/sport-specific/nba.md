# NBA Betting Guide

The NBA is the second most heavily bet sport in the US. It has the largest volume of games among the major American sports, provides extensive publicly available advanced metrics, and has structural features — particularly rest and travel — that are unusually well-documented and quantifiable. This makes it a fertile ground for model-based betting.

## Market Structure

The NBA regular season runs October through April with approximately 1,230 games (82 games × 30 teams / 2). Playoffs run April–June with up to 105 games.

At typical betting frequencies:
- A single-sport NBA bettor might place 300–600 bets per regular season
- Multiple seasons are still needed for statistical confidence — see [`variance-and-sample-size.md`](../variance-and-sample-size.md)

### Most Common Markets

- **Point spread**: typically -110 / -110; the most liquid market
- **Totals**: high-scoring sport (typically 215–235 combined points); very liquid
- **Moneyline**: large favorites (-300 and beyond) produce low-value moneyline bets; smaller underdogs offer better moneyline opportunity
- **Player props**: points, rebounds, assists, PRA combos — one of the best prop markets due to high-quality data

---

## Back-to-Back Games

The single most reliably impactful structural factor in NBA betting. A team playing their second game in two consecutive nights (a "back-to-back") performs measurably worse than in normal rest situations.

Historical impact (approximate):
- Back-to-back road games: largest negative effect, approximately -2 to -3 points vs. expectation
- Back-to-back home games: smaller negative effect, approximately -1 to -1.5 points
- Playing against a team on a back-to-back: positive effect for the rested opponent

**Most predictable impact**: road back-to-backs late in the season, when teams play conservatively to avoid injury risk.

**Load management interaction** (see below): star players often sit on back-to-back games, compounding the effect. Monitor injury reports for "rest" designations, especially for veteran stars.

### Constructing the Rest Feature

```python
rest_days_home = days_since_home_team_last_game  # 0 = back-to-back
rest_days_away = days_since_away_team_last_game
rest_differential = rest_days_home - rest_days_away
back_to_back_away = int(rest_days_away == 0)
back_to_back_home = int(rest_days_home == 0)
```

---

## Load Management

Load management refers to teams resting healthy star players to preserve them for the playoffs. It is unique to the NBA — you will not see a healthy Patrick Mahomes sitting out an NFL game, but you regularly see LeBron James or Kawhi Leonard "resting" for regular-season games.

**Impact on betting**:
- A team missing their best player(s) due to load management has dramatically different win probability
- The line often does not fully adjust before the news becomes public — there is a brief window of opportunity when a load management rest is confirmed
- Some books offer "player prop" refunds or voids when a player does not play; check each book's rules before betting props on players with known load management patterns

**Data source**: official injury reports (released ~1 hour before tip-off for load management decisions) and team beat reporter social media accounts are the fastest sources. The NBA's new rule requiring rest announcements by 5pm ET on game day has made this more predictable.

---

## Pace and Scoring Environment

The NBA total points market is heavily influenced by pace (possessions per game). A high-pace game between two high-pace teams produces more possessions and more scoring opportunities, directly translating to a higher expected total.

### Key Metrics

- **Pace**: possessions per 48 minutes (or per 100 possession-adjusted stats). Available from Basketball Reference.
- **Offensive Rating**: points scored per 100 possessions. Team OffRtg and DefRtg determine expected scoring.
- **Expected Total Formula**:

```
expected_total = ((home_OffRtg + away_DefRtg) / 2 + (away_OffRtg + home_DefRtg) / 2)
                 × (combined_pace / 100)
```

This gives a rough estimate of total expected points before adjusting for home/away effects, rest, and recent form.

### Totals as the Primary NBA Market

Many NBA modelers focus primarily on totals rather than spreads because:
- The pace and efficiency framework provides a clean, interpretable prediction
- Line movement is more predictable — public tends to bet overs; late-game totals often move down
- Injury adjustments are more straightforward (fewer possessions if a star sits; lower scoring)

---

## Home-Court Advantage

Historical NBA home-court advantage: approximately 3–3.5 points. Teams win roughly 59–60% of home games across the league.

**Factors that vary the advantage**:
- **Crowd intensity**: playoff atmosphere increases the advantage; late-season meaningless games decrease it
- **Team-specific**: some teams have notably stronger (Golden State, Boston Garden era) or weaker home advantages than league average
- **Altitude**: Denver's altitude (5,280 feet) is a known disadvantage for visiting teams — measurable effect on performance late in games due to fatigue

---

## Travel and Time Zones

Cross-country travel and time zone changes affect NBA teams more than NFL teams because:
- Games are played on consecutive nights; there is no week to recover
- The NBA season involves frequent transcontinental travel

**Key features**:
- Cross-country trip (East-West or vice versa): negative effect on road team, especially late in games
- 3-game western road swing: accumulated fatigue is measurable by game 3
- First game after a road trip (home): slight positive effect as teams return to familiar surroundings

---

## Lineup and Rotation Modeling

Unlike NFL (where starters are predictable) or MLB (where lineup is announced), NBA coaching rotations are fluid and affect per-possession efficiency significantly.

### Five-Man Lineup Data

The most granular NBA data is at the five-man lineup level — how each specific combination of five players performs together. This is available from Basketball Reference (lineups tab) and NBA Stats (official).

High-quality lineup data allows you to estimate the true performance impact of a player's absence (load management, injury) rather than using a rough "minus X points" adjustment.

### Starter/Bench Split

The gap between a team's starting five and bench performance varies widely. A team with a strong starting five and a weak bench is more vulnerable on back-to-back nights (when starters play fewer minutes) than a team with consistent depth.

---

## Modeling Approach

### Recommended Feature Set

| Feature | Why it matters |
|---------|----------------|
| Offensive rating differential | Efficiency-based strength estimate |
| Pace differential | Drives scoring environment for totals |
| Rest differential | Back-to-back effect |
| Back-to-back indicators (home/away) | Directional rest flags |
| Home-court advantage | ~3.5 points structural |
| Travel: time zone change | Cross-country disadvantage |
| Rolling 10-game OffRtg / DefRtg | Recent form, more weight than season average |
| Key player availability | Load management, injury status |
| Starter minutes share | Depth quality proxy |

---

## Resources

- **Basketball Reference**: comprehensive historical box scores, team ratings, lineup data
- **Cleaning the Glass**: opponent-adjusted efficiency metrics, position-specific defensive ratings (subscription, worth it)
- **NBA Stats** (stats.nba.com): official league data; lineup combinations, hustle stats, tracking data
- **PBP Stats** (pbpstats.com): play-by-play analysis, on/off splits
- **Second Spectrum** (team-level): full player tracking; aggregated metrics available via partnerships
