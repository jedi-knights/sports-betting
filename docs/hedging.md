# Hedging

Hedging means placing a bet on the opposite side of an existing open position to reduce or eliminate exposure to one or more outcomes. Done correctly, it locks in profit or limits loss. Done incorrectly — which is most of the time in practice — it sacrifices expected value in exchange for emotional comfort.

## When Hedging Makes Sense

There are exactly two mathematically justified reasons to hedge an existing bet:

1. **Your model's probability estimate has changed significantly** since you placed the original bet, and the new estimate makes the original position negative EV at current odds.
2. **Your bankroll situation has changed** such that the variance of the original position now exceeds what is appropriate given your current bankroll and Kelly sizing.

Every other reason to hedge is psychological, not mathematical. Recognizing the difference is the core discipline of this topic.

## The Basic Mechanics

Suppose you placed a bet before the season: Team A to win the championship at `+500` (6.0 decimal), staking $100. Potential profit: $500.

Mid-season, Team A reaches the final. The current odds for them to win are now `-200` (1.50 decimal). To fully hedge:

```
Hedge stake = original_potential_profit / (hedge_odds - 1)
            = 500 / (1.50 - 1)
            = $1,000
```

If you bet $1,000 on Team A to win at `-200`:
- If Team A wins: original bet pays $500 + $100 stake back = $600; hedge loses $1,000. Net: -$400.
- If Team A loses: original bet loses $100; hedge pays $1,000. Net: +$900.

Wait — the hedge loses money if Team A wins? This is a common confusion. The hedge here would be to bet **against** Team A (bet their opponent at favorable odds), not on Team A again.

Let me restate correctly for a futures hedge:

You hold: Team A to win at `+500`, $100 staked.
Team A's opponent is now priced at `+120` (2.20 decimal).

To hedge by betting the opponent:

```
Hedge stake = original_potential_return / hedge_decimal_odds
```

More generally, to lock in a specific profit `P`:

```
hedge_stake = (original_return - P) / (hedge_decimal_odds - 1 + 1)
            = (original_return - P) / hedge_decimal_odds
```

To lock in $200 guaranteed profit:

```
original_return = $600 (including $100 stake back)
hedge_stake = (600 - 200) / 2.20 = 400 / 2.20 ≈ $182

If Team A wins: +$500 (original) - $182 (hedge loss) = +$318
If opponent wins: -$100 (original) + $182 × 1.20 = -$100 + $218 = +$118
```

Hmm, the guaranteed lock-in formula requires setting both outcomes equal:

```
If A wins: 500 - hedge_stake = X
If B wins: -100 + hedge_stake × (2.20 - 1) = X

Solving:
500 - H = -100 + 1.20H
600 = 2.20H
H ≈ $273

If A wins: 500 - 273 = +$227
If B wins: -100 + 273 × 1.20 = -100 + 328 = +$228
```

A guaranteed $227–228 profit regardless of outcome, by betting $273 on the opponent.

## The Expected Value Cost of Hedging

Every hedge sacrifices expected value. Here is why.

At the time of the original bet, you accepted `+500` odds because your model estimated Team A's win probability was higher than the implied 16.7%. Suppose your model said 25%. EV = `0.25 × 500 - 0.75 × 100 = +$50`.

Now Team A is in the final. Their current win probability (from your model) is 55%. The hedge bet on the opponent is implied at `+120` = 45.5% probability. Your model says the opponent wins 45%. EV of hedge = `0.45 × (273 × 1.20) - 0.55 × 273 = 147.4 - 150.2 = -$2.8`. The hedge is slightly negative EV.

In general:
- If the hedge bet has positive EV by itself, place it regardless of the original position
- If the hedge bet has negative EV by itself, placing it sacrifices expected profit

The locked-in profit from the hedge is smaller than the expected value of the unhedged position. The hedge trades expected value for certainty.

**This trade is mathematically justified only when the variance of the unhedged outcome represents genuine bankroll risk** — i.e., a loss would impair your ability to continue betting at appropriate Kelly sizes.

## Practical Scenarios

### Scenario 1: Futures Bet Goes Well (Small Bankroll)

You have a $500 bankroll. You bet $50 on a futures outcome at `+1000`, now worth $500 if it hits. An unhedged loss would cost $50 (manageable). An unhedged win returns $500 (100% bankroll growth). From a Kelly perspective, you should likely let it ride — the position is already correctly sized.

### Scenario 2: Futures Bet Goes Well (Large Exposure)

You have a $2,000 bankroll. You bet $200 on a futures outcome at `+1000`, now worth $2,000 if it hits. A win doubles your bankroll; a loss costs $200 (10%). The exposure is still within reasonable bounds — hedging is probably not mathematically necessary, though acceptable if it represents a meaningful life-financial event.

### Scenario 3: Model Has Updated

Your original bet was placed when your model estimated Team A at 25%. After reviewing updated injury reports and recent performance, your model now estimates Team A at 15%. The current moneyline is `-150` (implied: 60%). The original bet now looks like it may have been based on outdated information. If the hedge bet on the opponent carries positive EV given your current model, place it — but this is independent bet logic, not hedging for comfort.

### Scenario 4: In-Game Hedging

You bet a team on the moneyline pre-game at `+200`. They take a 14-0 lead in the first quarter; the live line is now `-600`. Your original $100 bet is now worth ~$300 equivalent in live-market terms. Do you hedge?

At `-600` (implied 85.7%), the hedge has negative EV if your model says the team wins at 80%. The correct answer: only hedge if the unhedged variance impairs your bankroll materially, or if your live model genuinely believes the team wins at less than 85.7%.

## The Psychological Trap

Most hedges in practice are placed for emotional reasons:

- **Fear of "giving back" winnings**: the original profit feels real; the potential loss of it feels like a loss even though you have not received the money yet.
- **Loss aversion amplified by proximity**: as the game approaches, the outcome feels more vivid and threatening.
- **Narrative about "booking a profit"**: mentally accounting for the hedged return as "already secured."

These are all loss aversion and framing effects (see [`psychology-and-discipline.md`](psychology-and-discipline.md)). They cause real expected value sacrifice.

The discipline practice: before hedging, calculate the EV of both the current open position and the potential hedge bet explicitly. If the hedge is negative EV and your bankroll is not materially at risk, do not place it. Write down the calculation before acting.

## Partial Hedges

Rather than fully hedging (locking in a guaranteed amount), a partial hedge reduces — but does not eliminate — exposure:

```
partial_hedge_stake = full_hedge_stake × reduction_fraction
```

A 50% hedge on the above example: bet $136 on the opponent instead of $273. This produces an asymmetric outcome: more profit if Team A wins, less if Team A loses — but you have reduced variance by half.

Partial hedges make sense when the unhedged position is too large by Kelly criteria but you do not want to fully eliminate the position's upside.

## Key Takeaways

- A hedge is only mathematically justified when the open position now carries negative EV by your current model, or when the variance genuinely impairs your bankroll.
- Every hedge sacrifices expected value in exchange for reduced variance. Know what you are trading.
- Most hedges are placed for psychological comfort, not mathematical reasons. Pre-commit to a framework for evaluating hedges before you face the decision.
- Calculate the EV of both legs explicitly before deciding. The locked-in profit is always less than the expected value of the unhedged position (assuming the original bet was correctly priced).
