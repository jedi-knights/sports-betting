# Line Shopping and Account Management

Finding a positive-EV bet is only half the problem. Getting the best available price for it — and maintaining the accounts needed to do so — is the operational side of sports betting that separates professionals from casual bettors. A 2% edge evaporates quickly if you are consistently accepting worse-than-available odds.

## Line Shopping

Line shopping is the practice of comparing odds across multiple bookmakers to get the best available price for a given bet.

### Why It Matters

The difference between `-110` and `-105` on the same bet changes the break-even win rate from 52.38% to 51.22%. Over 1,000 bets, that is the difference between profit and loss on a model with only modest edge.

A more extreme example: if your model identifies a bet worth placing at any odds better than `-120`, but Book A offers `-125` and Book B offers `-110`, the correct choice at Book B produces 1.3% more EV per dollar wagered.

### Closing Line Value and Shopping

Consistently getting better prices than the closing line (positive CLV) is the strongest evidence of genuine edge. See [`market-efficiency.md`](market-efficiency.md). Line shopping directly improves your CLV by ensuring you always take the highest available price rather than the first available price.

### Tools for Line Shopping

**Odds aggregators** (show odds from multiple books on one screen):
- The Odds API
- OddsChecker
- Action Network
- Don Best (sharp-book focused, subscription)

**Exchanges** (Betfair, Sporttrade): exchanges post market-clearing prices with minimal margin. Use them as a benchmark for fair value and for hedging.

**Sharp book lines** (Pinnacle, Circa): these books set their own independent lines and do not limit sharp bettors. Their prices are the most efficient available and serve as a benchmark for soft books.

### Best Practices

- **Check 3–5 books** before placing any bet, not just your preferred book
- **Prioritize sharp books** for price anchoring (Pinnacle, Circa, BetOnline)
- **Use soft books** (DraftKings, FanDuel, BetMGM) for the best prices on public-heavy markets — they shade lines toward the public, which can create value on the other side
- **Track prices received** vs. closing lines on every bet — this is your CLV record

---

## Types of Bookmakers

Understanding the different types of books determines where to shop and what to expect.

### Sharp Books

Set their own independent lines. Accept large bets. Do not limit or ban profitable bettors. Their lines are considered the most accurate because they attract sharp action.

- **Pinnacle**: the gold standard. No limits, low margin (~2%), lines update rapidly. Available internationally but not in most US states.
- **Circa Sports**: US-facing sharp book, primarily Nevada and select states.
- **BetOnline / BookiePro**: sharp-oriented books with wider market access.

**Use for**: benchmarking fair value, placing large bets without fear of limitation.

### Soft Books (Recreational-Focused)

These books cater to recreational bettors. They offer promotions, accept small bets freely, but actively limit or ban accounts that show consistent profitability.

- **DraftKings, FanDuel, BetMGM, Caesars** (US)
- **Bet365, William Hill, Ladbrokes** (international)

**Use for**: getting the best price on markets they shade toward the public, taking advantage of promotions, line shopping.

**Avoid**: placing large bets consistently on the sharp side of the market. They will limit you.

### Betting Exchanges

Betfair, Sporttrade. You bet against other bettors, not the bookmaker. The exchange takes a commission (typically 2–5%) on net winnings.

- No theoretical limits (you are limited only by market liquidity)
- No banning — exchanges are neutral market makers
- Better prices on liquid markets than most soft books
- Essential for matched betting and laying (betting against an outcome)

---

## Account Management

### Setting Up a Multi-Book Operation

For serious betting, you need accounts at:
- 1–2 sharp books (for price benchmarking and large bets)
- 4–6 soft books (for shopping and promotions)
- 1 exchange (Betfair or Sporttrade where available)

Deposit funds across all accounts so you can move quickly when a price is available. Uneven funding forces you to miss bets because the right book has insufficient balance.

### Getting Limited

Soft books limit or ban accounts that show patterns consistent with sharp or professional betting. Common triggers:

- Consistently betting on the sharp side of line movements
- Taking early lines before they adjust
- Winning at an above-average rate over a meaningful sample
- Placing maximum bets on every sharp opportunity
- Arbing across books (see [`arbitrage-and-middles.md`](arbitrage-and-middles.md))

**Signs you have been limited**:
- Maximum bet sizes drop from $500 to $20
- Your bets are "pending review" for long periods
- Account is suspended without explanation

**Practical responses**:
- Do not bet your full model edge at soft books. Keep individual bet sizes modest relative to the book's normal limits.
- Mix in recreational bets (small parlays, same-game parlays) to appear less sharp
- Accept that soft book accounts have a finite lifespan and plan accordingly
- Prioritize sharp books and exchanges for larger bets

### Maintaining Sharp Book Access

Sharp books (Pinnacle, Circa) do not limit winners, but they adjust their lines when you bet — this is normal market functioning, not punishment. Accept it: their willingness to take your bet is part of the value. If your bet moves the line, it means you had genuine information.

### Account Security and Compliance

- Use strong unique passwords and 2FA on all accounts
- Keep records of all deposits, withdrawals, and betting activity for tax purposes (betting income is taxable in most jurisdictions)
- Be aware of jurisdiction-specific laws — legal sports betting varies dramatically by state and country
- Never share account credentials or allow others to bet on your account — this violates terms of service at every book

### Withdrawal Strategy

Keep the minimum necessary balance at each soft book — they are not banks and account closures can occur suddenly. Transfer winnings from soft books to sharp books or exchanges periodically. Most serious bettors maintain their primary working capital at sharp books and exchanges, drawing down soft book balances through regular withdrawals.

---

## Timing Your Bets

When you bet relative to the line opening affects both price and account longevity.

### Early Lines

Opening lines at sharp books are set with less information and are more likely to be mispriced. Betting early gives you the best price but also makes you identifiable as sharp. Soft books that see you consistently bet within the first hour of line posting will limit you faster.

### The Week Before Game Day (NFL)

NFL lines typically open Sunday night or Monday morning for the following week. The sharpest action hits immediately. By Thursday-Friday, the line has absorbed most professional money. By game day, the line reflects the maximum available information.

A general rule: for sharp model-based bets, earlier is better for price. For waiting on injury news or weather, later is necessary.

### Late Line Movement

Significant line movement in the final 24–48 hours often reflects sharp action or injury information. If your model does not incorporate this information but the market does, the late-moving line may actually be closer to true probability than your model's estimate. Factor this into bet-or-pass decisions.

---

## Record Keeping for Account Management

Beyond tracking bet performance, maintain a separate record for account management:

| Book | Balance | Limits encountered | Date of last bet | Notes |
|------|---------|-------------------|-----------------|-------|
| Pinnacle | $2,000 | None | 2024-09-10 | Primary sharp book |
| DraftKings | $500 | $50 max on NFL spreads | 2024-09-08 | Limit received Sept 2024 |
| Betfair | $1,500 | N/A (exchange) | 2024-09-09 | Primary for hedging |

This record tells you where you can still bet large, where you are limited, and which accounts need refreshing.
