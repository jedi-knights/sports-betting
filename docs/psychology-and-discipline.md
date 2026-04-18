# Psychology and Discipline

The mathematics of sports betting — expected value, Kelly sizing, calibration — only produces results if you execute your strategy consistently. The biggest threat to a profitable model is not the model itself but the human operating it. This document covers the cognitive biases that cause bettors to deviate from their strategies, and the discipline practices that professional bettors use to counteract them.

## Why Psychology Matters

A bettor with a genuine 5% edge who abandons their model after a 10-game losing streak will not profit. A bettor who increases bet sizes after a winning streak will blow up their bankroll despite being profitable. The model is only as good as the discipline with which it is followed.

This is not a character flaw — it is a predictable feature of human cognition. The biases below are universal. The solution is not to eliminate them (impossible) but to build systems that prevent them from affecting bet execution.

## Cognitive Biases

### Recency Bias

Overweighting recent outcomes relative to the full historical record.

**In practice**: a team loses three in a row and bettors pile onto the opponent, moving the line beyond what the underlying model justifies. The betting public treats a three-game sample as more informative than a season of data.

**How it affects you**: after your model produces 10 losing bets, you may start doubting it and deviating from recommendations — precisely when the model may still be correct and you are experiencing normal variance (see [`variance-and-sample-size.md`](variance-and-sample-size.md)).

**Countermeasure**: review the full historical backtest when doubting the model, not just recent results.

### Gambler's Fallacy

The belief that independent random events "balance out" — that a losing streak makes future wins more likely.

**In practice**: "the team is due for a win" after a losing streak. Each game is independent. The probability of winning the next game is unchanged by prior outcomes.

**In betting**: each bet's expected value is determined by the model's probability estimate vs. the market's, not by recent bet history.

**Countermeasure**: explicitly articulate why each bet has positive EV before placing it. Never reference prior streak in that justification.

### Hot Hand Fallacy

The inverse of gambler's fallacy: believing that a winning streak signals that future outcomes are also more likely to be wins.

**In practice**: a model goes 8-2 over 10 bets and you increase bet sizes beyond Kelly because you are "on a roll." The streak is statistical noise — the edge per bet has not changed.

**Countermeasure**: bet sizes are determined by the Kelly formula applied to each bet independently, not by recent performance.

### Confirmation Bias

Seeking out information that confirms your existing position and discounting information that contradicts it.

**In practice**: after placing a bet on Team A, you read the injury report for Team B and think "this confirms my bet" while mentally minimizing any news about Team A's injuries.

**In model development**: selecting features that confirm a theory rather than testing all candidate features impartially.

**Countermeasure**: generate predictions before reading game previews. Record the model's output before consuming media coverage of the game.

### Loss Aversion

Losses feel roughly twice as painful as equivalent gains feel good (a finding from behavioral economics). This causes irrational risk-averse behavior after losses and risk-seeking behavior to "get even."

**In betting**: chasing losses by placing larger bets than the model recommends to recover a deficit faster. This is one of the most common paths to bankroll ruin.

**Countermeasure**: treat the bankroll as a unit of long-run expected value, not a score to recover. Each bet's size is determined by Kelly applied to current bankroll — a reduced bankroll means reduced bet sizes, not increased ones.

### Availability Heuristic

Overweighting easily recalled events when estimating probabilities.

**In practice**: a team's dramatic last-second loss is more vivid in memory than five unremarkable losses. You overestimate how bad the team is because one outcome is more memorable.

**Countermeasure**: rely on model outputs rather than remembered narratives. The model weights all games equally; your memory does not.

### Anchoring

Over-relying on the first piece of information encountered when making decisions.

**In betting**: the opening line anchors your estimate of fair value. You may be reluctant to bet a team at `-150` even though your model says -200 is fair, simply because the opener was -120.

**Countermeasure**: generate your model's implied fair line before checking the bookmaker's line. Compare the two, do not let one contaminate the other.

### Narrative Fallacy

Constructing post-hoc stories that make outcomes feel inevitable, then using those stories to predict future outcomes.

**In practice**: "Team A lost because their QB had a bad week" — even if the data shows their loss was within normal variance. The story feels explanatory but has little predictive power.

**Countermeasure**: evaluate performance using models and statistics, not narratives. Narratives are often noise masquerading as signal.

---

## Discipline Practices

### Pre-Commitment

Decide your betting rules before the season starts and write them down:
- Which markets you will bet
- Minimum edge threshold for bet placement
- Maximum bet size as a fraction of bankroll
- The conditions under which you will review (not abandon) your model

Pre-commitment removes in-the-moment decision-making from the process. If the rule says "bet when model edge ≥ 3%," you bet — regardless of how you feel about the game.

### Separation of Model and Bet Execution

Generate model predictions before checking the bookmaker's line. This prevents anchoring and forces you to form an independent probability estimate.

Workflow:
1. Run model → record predicted probability
2. Convert to fair-odds line
3. Check available market odds
4. If edge ≥ threshold, place bet at the best available price

Never check the line first.

### Record Keeping

Maintain a complete betting log: date, sport, market, your model's probability, the odds taken, stake, result, and CLV. This is not optional — it is the only way to:

- Distinguish skill from variance objectively
- Identify which markets your model performs best in
- Detect model drift (calibration degrading over time)
- Provide evidence that disciplines you against emotional revision of history

### Bankroll Separation

Keep your betting bankroll entirely separate from personal funds. Physically separate accounts, not just mental accounting. When the bankroll is psychologically distinct, individual losses feel less threatening and loss-chasing is less tempting.

### Scheduled Reviews, Not Reactive Reviews

Review your model's performance on a fixed schedule (e.g., every 50 bets, or at the end of each month) — not in reaction to a losing streak. Reactive reviews lead to abandoning strategies during normal variance. Scheduled reviews allow you to distinguish normal variance from genuine model failure using the statistical tools in [`variance-and-sample-size.md`](variance-and-sample-size.md).

### The Kelly Discipline

Bet sizes are determined by the Kelly formula applied mechanically. They do not increase because you are on a winning streak. They do not increase to recover losses. They scale down as the bankroll shrinks and up as it grows — but always according to the formula, not your feelings. See [`bankroll-management.md`](bankroll-management.md).

### Defining Model Failure vs. Variance

Before the season, write down explicit criteria for concluding your model has failed (vs. experiencing normal variance):

- CLV is negative over 200+ bets → model is not finding value
- Z-score below -2.5 over 500+ bets → statistically significant underperformance
- Calibration on recent games shows systematic bias → model needs recalibration

These criteria, decided in advance, prevent emotional conclusions and provide an objective framework for model review.

---

## The Professional Mindset

Professional sports bettors consistently describe the same shift in perspective: they stop thinking about individual bets (which are effectively random) and start thinking about portfolios of bets over time (where edge compounds). 

A single losing bet is not evidence of a bad model. It is a single sample from a distribution. A single winning bet is not validation. The expected value of a bet is set when it is placed, based on your model's probability vs. the market's. The outcome is irrelevant feedback for any individual bet — only for large samples does the outcome distribution reveal whether your model is working.

This mindset is difficult to maintain under normal cognitive conditions. It requires the structural practices above — pre-commitment, separation, record keeping, scheduled reviews — to enforce consistently.
