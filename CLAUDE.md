# sports-betting — Claude Instructions

## Documentation Style

When writing or editing any Markdown file in this repository, cross-link related documents as much as possible. Every time a concept, model, or topic is mentioned that has its own document in `docs/`, link to it. This makes navigation easy on GitHub and helps a reader who is new to the field follow the thread between ideas.

- Prefer relative links: `[calibration](../calibration.md)` not an absolute path
- Link on first mention within each section, not every occurrence
- The glossary (`docs/glossary.md`) is the anchor reference — link to it when introducing a term that appears there

## Glossary Lookup Protocol

Whenever the user asks what something is (e.g., "what is a moneyline?", "what does vig mean?", "explain implied probability"), follow these steps before responding:

1. **Read `docs/glossary.md`** and search for the term.
2. **If the term is already defined**: answer directly using the glossary definition as your source, and note which section it appears in.
3. **If the term is not yet defined**:
   - Add a clear, beginner-friendly definition to the appropriate section in `docs/glossary.md`
   - Check all other documents in `docs/` (and `docs/models/`) for any that discuss the term in depth — add relative links from the new glossary entry to those documents
   - Then respond to the user using the definition you just wrote
4. **When adding or editing any glossary entry**: scan the existing docs for related documents and add links where relevant. The glossary is the navigation hub — entries for topics that have a dedicated document should always link to it.

Always read the glossary file first. Never answer a "what is" question in this repo from memory alone without first checking whether the glossary already has or needs an entry.

## Repository Context

This is a research and tooling repository for sports betting models. The owner is new to the field. When writing documentation, explain concepts clearly and define terms — do not assume prior knowledge of sports betting, statistics, or machine learning.

## Docker & Infrastructure Conventions

All backend services (Go) are containerized. Follow these rules consistently:

### Dockerfiles
- Every Go service has its own `Dockerfile` at `services/<name>/Dockerfile`
- Use multi-stage builds: a `builder` stage compiles the binary; a minimal `scratch` or `gcr.io/distroless/static` stage runs it
- No secrets, credentials, or data files are ever copied into an image

### docker-compose.yml
- A single `docker-compose.yml` at the repository root orchestrates all services and infrastructure
- Infrastructure services (PostgreSQL, etc.) are always defined here alongside the application services
- `docker compose up` must bring up the complete local development stack without additional steps
- Services that depend on the database declare `depends_on` with a `condition: service_healthy` healthcheck

### Data Persistence
- All persistent data (database files, file-based stores) uses **named Docker volumes**, never bind-mounted project directories
- Named volumes are declared in the `volumes:` block of `docker-compose.yml`
- Named volumes persist across `docker compose down` but are removed with `docker compose down -v` (document this clearly in README)
- The `data/` directory at the repository root is gitignored and may be used for local development exports, fixture CSVs, and test data — it is never mounted into a container

### Secrets and Environment
- `.env` files are gitignored — never commit them
- `.env.example` at the repository root documents every required environment variable with a placeholder value and a comment explaining its purpose
- Services read configuration exclusively from environment variables; no hardcoded credentials anywhere

### What is Never Committed
- `.env` and any `*.env` variant
- `data/` directory contents
- Database dumps or exports
- Container build artifacts

## Docs Structure

```
docs/
  glossary.md                  # term definitions — the anchor reference

  foundations/                 # understand the field before building anything
    odds-and-markets.md        # odds formats, bet types, vig
    value-betting.md           # core concept: positive EV
    market-efficiency.md       # closing line value, sharp vs. square
    variance-and-sample-size.md  # how many bets before conclusions are valid
    psychology-and-discipline.md # cognitive biases and execution discipline

  modeling/                    # building and evaluating predictive models
    calibration.md             # probability calibration — most important model property
    backtesting.md             # walk-forward validation, avoiding lookahead bias
    data-and-features.md       # data sources, feature engineering
    weather-modeling.md        # wind, precipitation, temperature effects by sport
    monte-carlo.md             # simulation techniques
    emerging.md                # RL, real-time inference, graph networks
    models/
      poisson.md               # goal-scoring model for soccer
      elo.md                   # dynamic team strength ratings
      logistic-regression.md   # baseline classification model
      quantile-regression.md   # spread/totals distribution modeling
      ml-methods.md            # XGBoost, Random Forests, ensembles

  strategy/                    # the mechanics of actually betting
    bankroll-management.md     # Kelly Criterion, bet sizing
    line-shopping-and-account-management.md  # getting the best price; account longevity
    prop-betting.md            # player proposition markets
    arbitrage-and-middles.md   # cross-book price exploitation
    hedging.md                 # reducing exposure on open positions
    tournament-and-playoff-modeling.md  # structural differences from regular season

  sport-specific/
    nfl.md                     # key numbers, weather, injury timing, DVOA
    nba.md                     # back-to-backs, load management, pace
    mlb.md                     # starting pitchers, park factors, platoon splits
    nhl.md                     # goaltenders, Corsi/xG, overtime structure
    soccer.md                  # Poisson application, xG, league selection, Asian handicap

  architecture/                # platform design — read before implementing anything
    README.md                  # bounded contexts, architectural decisions, implementation checklist
    data-models.md             # canonical type definitions for all contexts (Go + Python)
```
