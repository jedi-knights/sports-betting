# NHL Betting Guide

The NHL is the highest-variance major North American sport for betting purposes. Hockey is a low-scoring game (typically 5–7 total goals combined) where a single goaltender performance can dominate an entire game. The combination of low scoring, frequent ties needing extra time, and high goaltender variance makes NHL one of the most challenging sports to model — and also one of the more interesting for identifying inefficiencies.

## Market Structure

The NHL regular season runs October through April, with approximately 1,312 games (82 games × 32 teams / 2). Playoffs run April–June with up to 105 games.

### Bet Types

- **Moneyline**: most common; puck-line (spread) is secondary
- **Puck line**: NHL's version of a spread, almost always ±1.5 goals. Favorites at -1.5, underdogs at +1.5
- **Totals**: typically set at 5.5 or 6.5; occasionally 6.0 which allows pushes
- **3-way moneyline (regulation only)**: some books offer separate odds for home win/draw/away win in regulation, excluding overtime and shootout outcomes
- **Period betting**: first-period lines offer a pure early-game sample

### The Overtime/Shootout Structure

Every NHL game has a winner. After 60 minutes of regulation:
1. **5-minute 3-on-3 overtime**: if still tied, a shootout
2. **Shootout**: 3 rounds of penalty shots; if still tied, sudden death

Approximately 23–25% of NHL regular-season games go to overtime or shootout. This is critical for modeling:
- Puck-line favorites must win in regulation to cover -1.5 (OT/SO wins do not cover)
- Puck-line underdogs cover +1.5 in any regulation loss, plus any OT/SO loss (which counts as a 1-goal loss)
- 3-way moneylines price this differently — a team can "win" the moneyline but the 3-way prices regulation results separately

---

## Goaltender Dominance

No position in major sports has as much individual impact on game outcome as the NHL goaltender. The starting goaltender accounts for the majority of team-specific variance in goals allowed per game.

### Goaltender Quality Metrics

**Save Percentage (SV%)**: saves divided by shots faced. League average is approximately .910–.915. An elite goaltender might post .925+; a poor starter might be at .900.

**Goals Against Average (GAA)**: goals allowed per 60 minutes. Context-dependent — a goaltender behind a porous defense will have a worse GAA than their true talent would suggest.

**xGS% (Expected Goals Saved Percentage)**: compares actual saves to the expected saves given the quality of shots faced (from expected goals models). Better for isolating goaltender true talent from shot quality luck. Available from MoneyPuck, Natural Stat Trick.

**GSAx (Goals Saved Above Expected)**: the cumulative version — how many goals a goaltender has saved beyond what an average goaltender would have saved given the same shots. The best available single metric for goaltender quality.

### Goaltender Confirmation

NHL teams rarely announce their starting goaltender until approximately 1–1.5 hours before puck drop. A team's starter can change due to performance, injury, or coach's decision. This creates an information gap:

- Many bettors place NHL bets before the starter is confirmed
- If your model is starter-dependent (it should be), bet after the starter is confirmed, not before
- "Action" bets stand regardless of who starts; "listed goaltender" bets are voided if a different goaltender starts — always use listed goaltender options when available

---

## Back-to-Back Games

Like the NBA, the NHL regular season involves back-to-back games (a team playing on consecutive nights). The effect is similar but somewhat smaller than the NBA due to hockey's different physical demands.

Historical impact:
- Teams on back-to-back road games: approximately -1 to -1.5 points vs. expectation
- Backup goalies are more commonly used on back-to-back games — monitor roster decisions

### Goaltender on a Back-to-Back

If a team's starter played the night before and their backup is expected to start the second game, the expected goals-allowed rate increases significantly. Model this as a separate indicator: "starter-quality downgrade on back-to-back."

---

## Travel and Schedule

NHL teams often play 3–4 games in 5–6 days during certain stretches. Accumulated fatigue and cumulative travel distance is a predictive feature:

- The third game in 4 nights is the most fatigued state
- Teams playing their 4th or 5th consecutive road game show measurable fatigue
- The NHL schedule is geographically clustered by conference (East vs. West) which reduces the worst transcontinental travel, but cross-conference games still involve meaningful travel

---

## Home-Ice Advantage

Historical NHL home-ice advantage: teams win approximately 55% of home games in regulation. Converted to points in a model: approximately 0.3–0.5 goals per game — the smallest home advantage among the major North American sports.

The effect is larger in playoff contexts where crowd intensity is higher.

---

## Shot-Based Metrics (Corsi and Fenwick)

The most widely used NHL advanced metrics are shot-based:

**Corsi (CF%)**: percentage of all shot attempts (goals + shots on goal + missed shots + blocked shots) in a 5-on-5 situation directed toward the opponent's net. A team with a 55% Corsi is generating more shots and suppressing more shots than a team at 45% Corsi.

**Fenwick**: like Corsi but excluding blocked shots. Slightly more reflective of true shot quality access.

**These metrics are predictive** of future performance more than goals-based statistics over short sample sizes, because:
- Goals are high-variance (goaltender performance, shooting luck)
- Shot attempts are more stable and reflect territorial dominance

### Expected Goals (xG) in Hockey

Similar to soccer's xG (see [`sport-specific/soccer.md`](soccer.md)), NHL expected goals models weight each shot attempt by the probability it results in a goal based on location, shot type, and other factors.

**xGF% (Expected Goals For Percentage)**: the team's share of expected goals in 5-on-5 play. Better predictor of future performance than actual goals. Available from MoneyPuck, Natural Stat Trick.

---

## Special Teams

Power plays (5-on-4) and penalty kills are a meaningful portion of total goal scoring (~20% of goals come on special teams). Teams with elite power plays or penalty kills have a structural advantage.

**Power Play % (PP%)**: goals scored per power play opportunity. League average ~20%.
**Penalty Kill % (PK%)**: goals prevented per shorthanded situation. League average ~80%.

Special teams efficiency should be modeled separately from even-strength play, as the drivers (personnel, systems) differ.

### Penalty Rate

Some teams draw penalties at a higher rate than others (due to speed, puck possession style, or officiating tendencies). This is worth modeling as a feature — a team with a consistently high power play rate faces favorable conditions each game.

---

## Modeling Approach

### Recommended Feature Set

| Feature | Notes |
|---------|-------|
| Goaltender GSAx or xGS% | Primary quality signal; confirm starter first |
| Team xGF% (5-on-5, last 20 games) | Expected goals differential; more stable than goals |
| Corsi or Fenwick differential | Territory control proxy |
| Special teams differential (PP% - PK% gap) | Structural advantage |
| Back-to-back indicator | Rest/goaltender downgrade risk |
| Travel cumulative distance last 7 days | Fatigue proxy |
| Home/away | ~0.35–0.5 goal advantage |
| Season win% differential | Simple form signal |

---

## Resources

- **Natural Stat Trick** (naturalstattrick.com): Corsi, Fenwick, xG, shot charts, all split by situation; free
- **MoneyPuck** (moneypuck.com): expected goals model, goaltender metrics, team metrics; free
- **Hockey Reference** (hockey-reference.com): historical box scores, goaltender stats, team history; free
- **Evolving Hockey**: WAR (wins above replacement), RAPM (regularized adjusted plus-minus), goaltender models; partially free
