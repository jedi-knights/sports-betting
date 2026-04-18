# Emerging Directions

This document covers active research areas and trends in sports betting modeling that go beyond the classical approaches. These are not yet mainstream in practitioner toolkits, but they represent the frontier of where the field is moving.

## Multimodal Data Integration

Traditional models use structured tabular data: box scores, game results, betting lines. Emerging systems integrate multiple data modalities simultaneously.

### Video and Tracking Data

Player and ball tracking (from computer vision or optical tracking systems like Second Spectrum in the NBA or TrackMan in baseball) produces spatial and temporal data that tabular statistics cannot capture:

- Defensive positioning and coverage tendencies
- Ball movement patterns and spacing
- Biomechanical fatigue signatures (pace degradation, sprint distances)

Models trained on tracking data can identify performance changes before they show up in box scores, giving a short-term predictive edge.

**Challenge**: tracking data is expensive, proprietary, and requires significant preprocessing infrastructure before it can be used as model input.

### Natural Language Processing

News articles, press conference transcripts, and social media provide unstructured signals that sometimes precede line movements:

- Injury reports and health status updates
- Coaching strategy hints
- Team morale and locker room dynamics

NLP approaches (sentiment analysis, entity extraction, event detection) can surface this information programmatically.

**Challenge**: most of the signal is already incorporated into the line by the time it's publicly stated. The value lies in very fast parsing (seconds after an article publishes, not minutes) or in identifying nuanced signals that markets under-react to.

---

## Reinforcement Learning for Bet Sizing

The Kelly Criterion (see [`bankroll-management.md`](bankroll-management.md)) assumes static probability estimates and a single-bet-at-a-time decision. Real betting involves:

- A portfolio of simultaneous bets
- Correlated outcomes
- Unknown true probabilities (only model estimates)
- Sequential decisions where early outcomes affect available bankroll

Reinforcement learning (RL) frames bet sizing as a sequential decision-making problem:

- **State**: current bankroll, open bets, upcoming games, model confidence
- **Action**: bet size (and which market to bet)
- **Reward**: profit/loss
- **Policy**: learned mapping from state to action

RL agents can potentially learn bet-sizing policies that outperform fractional Kelly by adapting to the full correlational structure of a betting portfolio.

**Current status**: early-stage research. The major challenges are sample efficiency (sports seasons don't provide enough data for most RL algorithms to converge) and the non-stationarity of sports data (the environment changes year to year).

---

## Real-Time In-Game Inference

Live betting markets update continuously during a game. The edge window for any given model prediction is seconds to minutes before the bookmaker adjusts. Building a real-time inference system requires:

### Architecture Requirements

- **Low-latency data feed**: live score feeds, play-by-play events (often via WebSocket or streaming API)
- **Pre-computed game state representations**: models must run fast enough to generate predictions between events
- **Win probability model**: typically a combination of pre-game probability and in-game state (score, time remaining, possession)
- **Auto-execution or fast-alert system**: predictions must translate into bets before the market moves

### Win Probability Models

The most common live betting model computes win probability as a function of:
- Pre-game model probability
- Current score differential
- Time remaining
- Home/away
- Optional: momentum proxies (recent scoring rate, turnovers)

These can be implemented as lookup tables (pre-computed for all combinations of score differential × time remaining), simple regression models updated live, or Markov chain models that simulate the remaining game.

**Key insight**: in live markets, you are not competing against a human bookmaker's judgment. You are competing against an automated system's model. Finding the boundary conditions where automated live models are weakest (unusual game states, uncommon sports, first few minutes after a major event) is where edges exist.

---

## Portfolio-Based Bet Sizing

Rather than treating each bet independently, portfolio approaches size bets based on the full covariance structure of expected returns.

This is analogous to Markowitz portfolio optimization in finance:
- Individual bets are assets with expected returns (edge) and variance
- Correlations between bets reduce or increase effective risk
- The optimal portfolio maximizes the Sharpe ratio (expected return per unit of risk)

**Practical implementation**: requires estimates of cross-bet correlations (difficult to estimate reliably from limited data) and solving a quadratic optimization problem at bet time.

**Simpler version**: grouping bets by risk factor (same sport, same day, same team appearing in multiple bets) and applying a portfolio-level exposure cap to each group, rather than optimizing the full covariance matrix.

---

## Causal Inference

Most sports models are correlational — they identify features correlated with outcomes but cannot determine whether those features cause outcomes. Causal inference techniques try to establish actual causal relationships.

**Why it matters**: a feature correlated with wins only because it correlates with team quality (a confound) will degrade in predictive power when team quality changes. A causally valid feature (e.g., rest truly causes performance changes, not just that good teams happen to have different rest patterns) should be more stable over time.

Techniques from causal inference relevant to sports betting:
- **Difference-in-differences**: comparing outcomes before and after a change (e.g., rule change) across affected and unaffected teams
- **Instrumental variables**: finding exogenous variation (e.g., random schedule assignment) to isolate causal effects
- **Propensity score matching**: comparing teams that played on short rest vs. normal rest while controlling for other differences

This is an active area of sports analytics research and has not yet seen widespread adoption in betting model development.

---

## Graph Neural Networks

Teams and players form networks: players have relationships with teammates, coaches, and opponents. Graph neural networks (GNNs) can model these relationships explicitly:

- Representing a roster as a graph where nodes are players and edges represent on-court/on-field relationships
- Learning how player interaction quality affects team performance
- Capturing the effect of trades and lineup changes more accurately than simple aggregation

GNNs have shown promise in soccer (player interaction networks from passing data) and basketball (lineup effect modeling), but require more data and specialized infrastructure than classical approaches.

---

## Practical Horizon

For most practitioners, the classical approaches (Poisson models, Elo, logistic regression, XGBoost with good features) still represent the most accessible path to building a profitable model. The emerging approaches above are most relevant to:

- Teams with access to expensive proprietary tracking data
- Well-funded operations that can afford the engineering infrastructure for real-time inference
- Academic researchers exploring the theoretical limits of sports prediction

As these techniques mature and the required data becomes more accessible, they will likely become standard components of practitioner toolkits. The most immediately actionable emerging direction for a small operation is **real-time in-game inference** in niche markets where automation infrastructure is less mature.
