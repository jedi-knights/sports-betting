# Sport-Specific Guides

Each document in this section is a self-contained reference for one sport. The guides apply the general frameworks from [Foundations](../foundations/README.md), [Modeling](../modeling/README.md), and [Strategy](../strategy/README.md) to each sport's specific structure, data sources, key metrics, and structural features that affect model design.

## Overview by Sport

### [NFL](nfl.md)

The most heavily bet sport in the United States and one of the most efficiently priced markets in the world. The NFL has well-understood structural features that every model must account for.

**What makes NFL unique for betting:**
- **Key numbers**: certain victory margins (3, 7, 10) occur far more frequently than others due to the scoring system. A spread at -3 is worth significantly more than -3.5. Buying or selling half-points at key numbers is one of the most tractable edges in NFL betting.
- **Weather**: wind above 20 mph reduces expected totals by 3–5 points. The most reliable weather effect in any major sport.
- **Injury information windows**: the Wednesday/Thursday/Friday practice report progression creates a predictable information timeline. The highest-value window is Friday–Saturday when final designations drop.
- **Recommended metrics**: DVOA (Football Outsiders), EPA per play (nflfastR), Elo ratings
- **Primary data source**: nflfastR (free play-by-play going back to 1999)

---

### [NBA](nba.md)

The second most heavily bet sport in the US with the highest game volume of any major American sport, giving modelers the most data per season. The NBA has the most measurable and predictable structural inefficiency of any major sport: rest and travel effects.

**What makes NBA unique for betting:**
- **Back-to-back games**: the single most reliable NBA modeling feature. Teams on their second game in two nights — especially on the road — perform measurably worse, approximately -2 to -3 points vs. expectation.
- **Load management**: star players routinely sit out regular-season games for rest. Official NBA rest announcements are required by 5pm ET on game day; monitor beat reporters for earlier signals.
- **Pace and efficiency framework**: totals markets are cleanly modeled by combining both teams' offensive and defensive ratings with pace. A high-pace game between two efficient offenses has a predictably higher total.
- **Recommended metrics**: offensive/defensive rating (Basketball Reference), opponent position ratings (Cleaning the Glass), lineup data (NBA Stats)
- **Primary data source**: Basketball Reference, Cleaning the Glass (subscription), PBP Stats

---

### [MLB](mlb.md)

The highest-volume sport for data (162 games per team, 2,430 total regular-season games) and the most pitcher-dominated sport for betting. The starting pitcher matchup is more determinative of a single game's outcome than any equivalent factor in another major sport.

**What makes MLB unique for betting:**
- **Starting pitcher dominance**: the single most important variable in any MLB game prediction. Always use xFIP or SIERA (fielding-independent metrics) rather than ERA for pitcher quality estimation.
- **Park factors**: ballpark dimensions, altitude (Coors Field), and atmospheric conditions vary dramatically. Raw team statistics without park adjustment are misleading.
- **Platoon splits**: most batters perform meaningfully better against opposite-hand pitchers. A lineup heavy with right-handed batters facing a left-handed starter creates a quantifiable disadvantage.
- **First 5 innings (F5) bets**: removes bullpen variance and isolates the starting pitcher matchup — often the cleanest way to bet a specific pitcher.
- **Recommended metrics**: xFIP, SIERA (FanGraphs), Statcast data (Baseball Savant), park factors (Baseball Reference)
- **Primary data source**: Baseball Savant (Statcast), FanGraphs, Baseball Reference

---

### [NHL](nhl.md)

The highest-variance major North American sport for betting. Low scoring (5–7 combined goals typical), frequent overtime and shootout games (~25% of regular-season games), and extreme goaltender dependence make NHL one of the most challenging sports to model.

**What makes NHL unique for betting:**
- **Goaltender dominance**: the starting goaltender's quality is the most important single variable. Starters are typically not confirmed until 60–90 minutes before puck drop — always use "listed goaltender" bet options and confirm the starter before placing.
- **Overtime/shootout structure**: ~25% of regular-season games go to OT or shootout. This has direct implications for puck-line betting (favorites must win in regulation to cover -1.5) and for 3-way moneyline markets.
- **Shot-based metrics**: Corsi% and xGF% (expected goals for percentage) are more stable predictors of future performance than actual goals in small samples because goals are high-variance.
- **Back-to-backs**: similar to NBA but smaller effect; primarily relevant when forcing a backup goaltender to start.
- **Recommended metrics**: xGF% (MoneyPuck), GSAx (goals saved above expected, MoneyPuck), Corsi (Natural Stat Trick)
- **Primary data source**: Natural Stat Trick (free), MoneyPuck (free), Evolving Hockey

---

### [Soccer](soccer.md)

The world's most bet sport by volume, with thousands of leagues across every continent. The sport for which the Poisson model was specifically developed. Offers the most market variety (1X2, Asian handicap, correct score, BTTS, totals) and the most publicly available research.

**What makes soccer unique for betting:**
- **The draw**: soccer's third match outcome (~27% of matches in top leagues) is where the most calibration work is needed. Bookmakers often price draws less precisely than win markets.
- **Expected goals (xG)**: the most important advanced metric. Teams that score goals without high xG are benefiting from luck that regresses; teams with high xG and few goals will "catch up." xG differential is the strongest predictor of future league standings.
- **League selection**: top leagues (Premier League, Bundesliga, La Liga) have high data quality and high market efficiency. Lower leagues have worse data but lower efficiency — more potential edge if you can get reliable data.
- **Asian handicap markets**: lower bookmaker margins (2–3%) than 1X2 markets (4–6%), and eliminates the draw as a separate outcome — useful for applying a two-outcome model directly.
- **Recommended metrics**: xG (Understat, FBref), attack/defense ratings (Poisson model fitted to historical results)
- **Primary data source**: Understat (xG, free), FBref (StatsBomb data, free), football-data.co.uk (historical odds, free)

## How to Use These Guides

Each guide is structured as a reference document, not a tutorial. Use it to:

1. **Understand the structural features** of the sport before designing a model — key numbers, home field, rest effects, etc.
2. **Select appropriate metrics** for the sport — not all advanced metrics transfer across sports
3. **Find the right data sources** — each guide lists free and paid sources ranked by usefulness
4. **Check your feature set** against the recommended table in each guide

## Cross-References

All sport-specific guides link back to the relevant general documents:
- Model recommendations link to [Modeling/Models](../modeling/models/README.md)
- Feature engineering links to [Data and Features](../modeling/data-and-features.md)
- Weather effects link to [Weather Modeling](../modeling/weather-modeling.md)
- Playoff considerations link to [Tournament and Playoff Modeling](../strategy/tournament-and-playoff-modeling.md)
- Sample size guidance links to [Variance and Sample Size](../foundations/variance-and-sample-size.md)
