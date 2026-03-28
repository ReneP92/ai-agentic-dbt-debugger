# ai-agentic-dbt-debugger

A self-contained dbt project running against a [LocalStack Snowflake](https://docs.localstack.cloud/snowflake/) emulator, designed as a sandbox for building and testing an AI agent that debugs dbt pipelines.

## Architecture

```
┌──────────────────────────────────────────────────┐
│  Docker Compose (dbt-net bridge network)         │
│                                                  │
│  ┌────────────────────┐  ┌────────────────────┐  │
│  │  localstack        │  │  dbt               │  │
│  │  (Snowflake emu)   │◄─┤  (Python 3.12)     │  │
│  │  Port 4566         │  │  dbt-snowflake     │  │
│  │                    │  │  1.9.1             │  │
│  └────────────────────┘  └────────────────────┘  │
└──────────────────────────────────────────────────┘
```

**LocalStack Snowflake** emulates a Snowflake warehouse locally so no cloud account is needed. The **dbt** container runs as a long-lived sidecar (`tail -f /dev/null`) and all commands are issued via `docker compose exec`.

## Data Model

The project models a **betting platform** with three raw source tables seeded on startup:

| Table | Rows | Description |
|---|---|---|
| `RAW.USERS` | 15 | Users across GB/US/DE with GBP/USD/EUR currencies |
| `RAW.BETS` | 15 | Mix of settled (won/lost/void) and open bets |
| `RAW.TRANSACTIONS` | 35 | Coherent financial ledger (deposits, bet debits, winnings, withdrawals, refunds) |

### dbt Layer Architecture

```
RAW (source)
  └── Standardised (views) ── type casting, normalisation, no business logic
        ├── std_user
        ├── std_bet
        └── std_transaction
              └── Conformed (tables) ── business logic, joins, derived attributes
                    ├── dim_user          (is_kyc_verified, is_active, registration_device)
                    └── fct_bet           (gross_gaming_revenue, is_same_day_settled)
                          └── Mart (tables) ── aggregations for consumption
                                └── mart_bet_daily   (daily metrics by sport/bet_type/currency/country)
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- A [LocalStack auth token](https://app.localstack.cloud/) (free trial available)

## Quick Start

1. **Clone and configure:**

   ```bash
   git clone <repo-url>
   cd ai-agentic-dbt-debugger
   cp .env.example .env
   # Edit .env and add your LOCALSTACK_AUTH_TOKEN
   ```

2. **Build and start:**

   ```bash
   make build
   make up
   ```

   This starts the LocalStack Snowflake emulator and the dbt container. On startup, the init script (`localstack/init/ready.d/01_seed.py`) automatically creates the `BETTING` database, schemas, tables, and seed data.

3. **Verify the setup:**

   ```bash
   make dbt-debug    # Verify dbt can connect
   make inspect       # Print schema + sample rows for all tables
   ```

4. **Run the dbt pipeline:**

   ```bash
   make dbt-deps     # Install dbt packages (dbt_utils)
   make dbt-build    # Run models + tests in one pass
   ```

5. **Inspect the results:**

   ```bash
   make inspect       # Now shows raw + standardised + conformed + mart tables
   ```

## Makefile Targets

### Infrastructure

| Target | Description |
|---|---|
| `make build` | Build all Docker images |
| `make up` | Start all services (detached) |
| `make down` | Stop and remove containers |
| `make restart` | Restart all services |
| `make logs` | Follow logs for all services |
| `make ps` | Show container status |
| `make clean` | Remove containers, volumes, and images |

### dbt

| Target | Description |
|---|---|
| `make dbt-debug` | Verify dbt can connect to LocalStack Snowflake |
| `make dbt-deps` | Install dbt packages (`dbt deps`) |
| `make dbt-run` | Run all dbt models |
| `make dbt-test` | Run all dbt tests |
| `make dbt-build` | Run dbt build (models + tests in one pass) |
| `make dbt-shell` | Open an interactive shell in the dbt container |
| `make inspect` | Print schema + 10 random rows for every table |

## Project Structure

```
.
├── Makefile                          # All commands
├── docker-compose.yml                # LocalStack + dbt services
├── .env.example                      # Template for secrets
├── dbt/
│   ├── Dockerfile                    # Python 3.12 + dbt-snowflake 1.9.1
│   ├── dbt_project.yml               # dbt project config
│   ├── profiles.yml                  # Connection to LocalStack Snowflake
│   ├── packages.yml                  # dbt_utils dependency
│   ├── scripts/
│   │   └── run_dbt.sh                # Wrapper that captures JSON logs + manifest
│   └── models/
│       ├── sources/
│       │   └── schema.yml            # Raw source definitions
│       ├── standardised/
│       │   ├── std_user.sql
│       │   ├── std_bet.sql
│       │   ├── std_transaction.sql
│       │   └── schema.yml
│       ├── conformed/
│       │   ├── dim_user.sql
│       │   ├── fct_bet.sql
│       │   └── schema.yml
│       └── mart/
│           ├── mart_bet_daily.sql
│           └── schema.yml
├── localstack/
│   └── init/
│       └── ready.d/
│           └── 01_seed.py            # Database + schema + seed data init hook
├── scripts/
│   └── inspect_data.py               # Utility to introspect tables in LocalStack
└── logs/
    └── dbt/                          # Bind-mounted dbt logs (gitignored)
```

## run_dbt Wrapper

All `dbt-run`, `dbt-test`, and `dbt-build` commands go through the `run_dbt` wrapper script, which:

- Runs dbt with `--log-format json` for structured output
- Captures logs to `logs/dbt/runs/<run_id>.log`
- Writes a manifest to `logs/dbt/runs/<run_id>.manifest.json` with run metadata (exit code, success flag, timestamps)

This structured output is designed for consumption by an AI debugging agent.

## Troubleshooting

**`database "BETTING" does not exist`** -- The LocalStack init scripts may not have finished running. Wait a few seconds after `make up` and try again. The `inspect` script has built-in retry logic (5 attempts, 3s apart).

**`make clean` then `make up`** -- For a completely fresh start, this tears down all containers and volumes and rebuilds from scratch.

**Checking init script status:**

```bash
docker compose logs localstack | grep "seeded successfully"
```

You should see `BETTING database seeded successfully.` in the output.
