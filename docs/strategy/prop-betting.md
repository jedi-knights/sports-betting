# Prop Betting

Prop bets (proposition bets) are wagers on specific events within a game that don't directly relate to the final score or winner. They include things like how many rushing yards a player will have, whether a specific player will score a touchdown, or how many strikeouts a pitcher will record. Props are one of the fastest-growing markets in sports betting and, for model-driven bettors, often offer more exploitable edges than game lines.

## Why Props Offer More Edge

Game lines in major sports (NFL spreads, NBA totals) are among the most efficiently priced markets in the world — thousands of sharp bettors and sophisticated bookmaker models price them very accurately. Player props are different:

- **Higher bookmaker margins**: props typically carry 8–15% overround vs. 4–5% for game lines
- **Less sharp action**: fewer professional bettors focus on player-level statistics, so mispricings persist longer
- **More bookmakers, less synchronization**: soft books often set their own prop lines independently rather than copying sharp book lines, creating cross-book discrepancies
- **Information asymmetry**: injury status, role changes, and matchup-specific data are less efficiently incorporated into prop lines than into game lines

The higher margin is a tax. But the lower market efficiency more than compensates for it in well-modeled markets.

## Major Prop Categories

### Player Performance Props

The most common and most liquid props:

**NFL**:
- Passing yards, touchdowns, interceptions
- Rushing yards, rushing touchdowns
- Receiving yards, receptions (player receptions are particularly popular since the legalization of "anytime scorer" markets)

**NBA**:
- Points, rebounds, assists
- Points + rebounds + assists (PRA) combos
- Threes made, steals, blocks
- Double-double / triple-double

**MLB**:
- Pitcher strikeouts (one of the most modeled props)
- Hits, RBIs, home runs
- Total bases

**NHL**:
- Shots on goal
- Points (goals + assists)
- Goals

### Game Props

Bets on specific game events rather than player performance:
- First team to score
- Team to score in a specific quarter/half
- Exact score combinations
- Number of penalties, corner kicks (soccer)

### Novelty/Entertainment Props

Super Bowl-adjacent props: length of the national anthem, first commercial shown, halftime show outcomes. These are typically priced with very high margins and are not amenable to systematic modeling.

---

## Building a Player Props Model

### Step 1: Establish a Player Baseline

For each player, estimate their expected performance using their recent history:

- Rolling average over last 5, 10, 20 games (different weights depending on recency preference)
- Season-to-date average adjusted for context (minutes played, usage rate in basketball; snap count in NFL)
- Career baseline for regression purposes on small samples

### Step 2: Adjust for Matchup

Opponent quality affects player performance differently depending on the sport:

**NBA**: defensive rating (points allowed per 100 possessions), plus position-specific defensive metrics (e.g., points allowed to opposing point guards). Sources: Cleaning the Glass, Basketball Reference.

**NFL**: target share of defensive coverage, yards allowed per route run by coverage type. Sources: PFF (premium), NextGenStats, Sharp Football.

**MLB**: pitcher-specific metrics (ERA, xFIP, strikeout rate, velocity trends). Matchup adjustments should use platoon splits (lefty vs. righty).

A multiplicative adjustment is common:

```
adjusted_projection = baseline × (opponent_defensive_metric / league_average)
```

### Step 3: Adjust for Game Context

Situational factors that affect expected player performance:

- **Pace** (basketball): teams playing faster give all players more counting-stat opportunities
- **Game script** (NFL): a team expected to trail will pass more; a team expected to lead will run more
- **Implied total** (all sports): high over/under suggests a high-scoring game, which benefits offensive players
- **Vegas spread**: heavy favorites will likely play their starters fewer minutes in a blowout

### Step 4: Model the Distribution

The bookmaker sets a line (e.g., "Player X: over/under 24.5 points"). You need `P(player scores > 24.5)`.

For integer-valued counting stats (points, strikeouts, rebounds), a Poisson or negative binomial distribution around your projected mean works well. For continuous stats (passing yards, rushing yards), a normal or log-normal distribution is appropriate.

```
P(player > line) = 1 - CDF(line; mean=projection, distribution_params)
```

Compare this probability to the implied probability from the bookmaker's odds. If your model says 58% and the implied odds say 50%, you have a value bet on the over.

### Step 5: Handle Half-Point Lines

Player props are often set at half-integer lines (24.5, 7.5) to eliminate pushes. This means you need accurate probability mass at the integer boundaries:

- A line of 24.5 is equivalent to asking "does the player score 25 or more?"
- A line of 25.0 produces a push at exactly 25 — your model should account for the probability of that exact outcome

---

## Data Sources for Player Props

| Sport | Data Source | Key Metrics |
|-------|------------|-------------|
| NBA | Basketball Reference | Box scores, advanced stats, historical lines |
| NBA | Cleaning the Glass | Opponent position ratings, adjusted stats |
| NFL | Pro Football Reference | Historical play-by-play, snap counts |
| NFL | NextGenStats (free) | Target share, air yards, separation |
| NFL | PFF (premium) | Route running, coverage grades, blocking |
| MLB | Baseball Savant / Statcast | Spin rate, exit velocity, xFIP, whiff rate |
| MLB | Baseball Reference | Historical splits, platoon data |
| NHL | Natural Stat Trick | Shot rates, Corsi, expected goals |
| All | The Odds API | Historical prop lines from multiple books |

---

## Correlated Props and Same-Game Parlays

Player props within the same game are correlated. If a quarterback is projected to throw for 350 yards, his wide receivers are likely to have strong receiving yards totals. Bookmakers price individual props assuming independence but offer same-game parlays (SGPs) at reduced odds that account for correlation.

### Implications

- **Individual prop models can exploit correlation**: if you believe the game will be high-scoring, betting all relevant offensive props may each carry positive EV independently
- **SGPs are almost always negative EV**: bookmakers set SGP odds to be worse than the product of individual probabilities adjusted for correlation; they retain a significant margin
- **Identifying uncorrelated props**: some props within a game are largely uncorrelated (e.g., punter gross yards and a quarterback's touchdowns), which occasionally creates SGP opportunities

---

## Common Pitfalls

**Small sample sizes**: player performance is high-variance. A running back's 5-game rushing average is not reliable. Use longer windows and regress toward the mean aggressively for players with fewer data points.

**Injury and role changes**: a player returning from injury, transitioning to a new team, or changing roles within an offense may have misleading historical data. Build mechanisms to flag these situations.

**Bookmaker line quality**: prop lines at soft books are sometimes set formulaically and adjusted less frequently than game lines. This creates opportunity but also means late-breaking information may not be reflected — always check if recent news (injury update, lineup change) has moved the line.

**Stacking errors**: if your projection model and your distribution model both have errors in the same direction, the compounded error on the probability estimate can be large. Validate both independently.
