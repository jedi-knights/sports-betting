# Market Efficiency

A sports betting market is efficient if the bookmaker's odds accurately reflect all available information. In an efficient market, there is no systematic way to find positive expected value — any model you build will fail to beat the market consistently after accounting for the vig.

Understanding market efficiency is crucial because it tells you where to look for edges, how quickly those edges disappear, and what evidence to use when evaluating whether your model is genuinely profitable.

## The Efficient Market Hypothesis in Sports

Borrowed from financial economics, the Efficient Market Hypothesis (EMH) applied to sports betting says: at any point before a game, the offered odds represent the market's best estimate of the true probability, incorporating all publicly available information.

In practice, markets are not perfectly efficient, but some are far more efficient than others. The degree of efficiency depends on:

1. **Market liquidity**: how much money flows through it. NFL moneylines and NBA totals are highly liquid; Estonian lower-division soccer is not.
2. **Sharp action**: whether professional bettors actively arbitrage away mispricings.
3. **Information availability**: whether key data (injuries, weather, lineup changes) is widely accessible and quickly incorporated.

## The Closing Line as the Efficiency Benchmark

The **closing line** — the final odds posted just before game time — is the most efficient price available. By then, all public information has been incorporated, injury news has been processed, and professional bettors have had the maximum opportunity to move the line.

This makes the closing line the best available approximation of the true probability. Beating the closing line (i.e., getting better odds than the closing price) is therefore a strong signal that your model has genuine predictive edge.

## Closing Line Value (CLV)

**Closing Line Value** is the difference between the odds you obtained when placing a bet and the closing line odds.

If you bet Team A at `+120` and the game closes at `+105`, you got `+15` cents of value — you beat the closing line. If you bet at `+120` and it closes at `+130`, the line moved against you.

CLV calculation (in terms of implied probability):

```
CLV = closing_implied_probability - your_bet_implied_probability
```

Positive CLV means you got a better price than the closing line (favorable for you).

### Why CLV Matters More Than Short-Run Wins

A bettor with genuine edge should consistently beat the closing line. Why? Because:

1. The closing line is the most accurate probability available
2. If your bet regularly gets better prices than the closing line, you are consistently finding edges that the market later corrects
3. A bettor who beats CLV but loses money is likely experiencing bad variance, not a broken model
4. A bettor who wins money but has negative CLV is likely getting lucky — the model is not actually identifying edges

**Professional sharp bettors use CLV as their primary performance metric**, evaluating model quality over sample sizes of thousands of bets, not short-run win/loss records.

## Types of Market Inefficiency

### Informational Inefficiency

The market hasn't yet incorporated available information. This window is shortest in highly liquid markets (NFL game lines update within minutes of an injury report) and largest in less-watched markets.

Exploiting this requires:
- Access to information early (often through subscriptions to injury databases, weather services, or analytics platforms)
- Fast execution before the market adjusts

### Analytical Inefficiency

The market has access to the same information but has systematically mispriced it. This is rare in efficient markets but more common in props, futures, and lower-tier leagues where bookmakers use less sophisticated models.

Exploiting this requires:
- A model that is genuinely better than the bookmaker's pricing model
- Persistence — analytical edges erode as bookmakers improve their models

### Structural Inefficiency (Public Bias)

Recreational bettors systematically overbet certain outcomes:
- Popular teams (Yankees, Cowboys, Lakers)
- Home favorites
- Heavy favorites (people like "safe" bets)
- Round totals (49.5 sees more over action than 49 does)

Bookmakers exploit this by shading lines toward where they expect more public action, which may leave the other side mispriced. This is not purely an inefficiency — bookmakers do this intentionally to balance their books — but it creates predictable patterns.

## Sharp vs. Square Action

### Sharps (Professional Bettors)

Sharps bet large amounts, are selective, and have demonstrated long-run profitability. Bookmakers track sharp accounts and move lines quickly when they bet. Consistent sharp action in one direction is a meaningful signal about true probability.

Signs of sharp action:
- Large single wagers on a specific side
- Line movement opposite to public betting percentages (reverse line movement)
- Simultaneous line movement across multiple bookmakers (steam move)

### Squares (Recreational Bettors)

Squares bet more frequently, on more games, and are more influenced by media narratives and team familiarity than statistical analysis. Their collective action can move lines in soft books, but they are net losers and do not contribute useful information.

### Using Sharp Action as a Signal

Some models incorporate line movement direction as a predictor: if a line moves in a direction that appears to contradict public percentages, it may indicate sharp action that is more informative than the public. This approach (fade the public, follow the sharps) has mixed empirical support and varies significantly by sport and time period.

## Market Efficiency by Sport and Market Type

| Market | Efficiency | Notes |
|--------|-----------|-------|
| NFL spreads | Very high | Heavily bet; closing line is highly accurate |
| NBA totals | High | Large volume; in-game adjustments are fast |
| MLB moneylines | High | But less sharp action on individual games than NFL/NBA |
| NHL moneylines | Moderate | Lower volume than football/basketball |
| Soccer (top leagues) | High | High international volume and sophisticated bookmakers |
| Soccer (lower leagues) | Low to moderate | Thinner markets, less information efficiency |
| Player props | Moderate | Higher bookmaker margins; less sharp action |
| Futures | Low to moderate | High margins; difficult to analyze efficiently |
| Live betting | Varies | Speed matters enormously; slow bettors face negative CLV |

## Practical Implications

1. **Model against the market, not against the outcome**: your model's job is to predict probability more accurately than the bookmaker, not just to predict winners.

2. **Track CLV on every bet**: this is the only reliable way to distinguish genuine edge from variance over reasonable sample sizes.

3. **Target inefficient markets**: if your analytical edge is modest, apply it in markets with higher margins (props, futures, lower leagues) where the bookmaker's models are weaker.

4. **Act early**: edges are largest immediately after lines open and shrink as sharp money moves the market toward efficiency. For some markets, the best odds are gone within minutes of posting.

5. **Expect to be limited**: bookmakers ban or severely limit profitable bettors. Building and maintaining accounts across multiple books is a necessary operational reality for any serious operation. See [`data-and-features.md`](data-and-features.md) for notes on account management.
