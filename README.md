# ai-agentic-dbt-debugger

A self-contained dbt project running against a [LocalStack Snowflake](https://docs.localstack.cloud/snowflake/) emulator, with an AI agent system that automatically investigates dbt pipeline failures and creates structured failure tickets.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Docker Compose (dbt-net bridge network)                            │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  localstack       │  │  dbt             │  │  agent           │  │
│  │  (Snowflake emu)  │◄─┤  (Python 3.12)   │  │  (Python 3.12)   │  │
│  │  Port 4566        │  │  dbt-snowflake   │  │  Strands Agents  │  │
│  │                   │  │  1.9.1           │  │  Claude Sonnet 4 │  │
│  └──────────────────┘  └────────┬─────────┘  └───┬──────┬───────┘  │
│                                 │  logs/dbt (rw)  │ (ro) │          │
│                                 └────────┬────────┘      │          │
│                                          │               │          │
│                                  ┌───────▼───────┐       │          │
│                                  │  logs/dbt/    │       │          │
│                                  │  runs/        │       │          │
│                                  └───────────────┘       │          │
│                                                          │          │
│                                  ┌───────────────┐       │          │
│                                  │  output/      │◄──────┘          │
│                                  │  tickets/     │  (rw)            │
│                                  └───────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

**LocalStack Snowflake** emulates a Snowflake warehouse locally so no cloud account is needed. The **dbt** container runs as a long-lived sidecar and all commands are issued via `docker compose exec`. The **agent** container runs the AI debugging agent -- it reads dbt logs and model SQL (read-only) and writes failure tickets to `output/tickets/`.

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

## Agent System

The agent system reacts to dbt run failures. When a dbt command exits non-zero, a wrapper script invokes the AI agent to investigate the failure and produce a structured ticket.

### How It Works

```
dbt run fails
      │
      ▼
scripts/dbt_with_agent.sh
      │  detects non-zero exit, extracts run_id from latest manifest
      ▼
┌─────────────────────────────────────────────┐
│  Orchestrator Agent                         │
│  (reads manifest, logs, model SQL)          │
│                                             │
│  Tools:                                     │
│    read_dbt_manifest  ── run metadata       │
│    read_dbt_logs      ── error/warn entries  │
│    read_model_sql     ── source SQL          │
│    ticket_agent       ── sub-agent (below)   │
└──────────────────┬──────────────────────────┘
                   │  delegates with full context
                   ▼
┌─────────────────────────────────────────────┐
│  Ticket Creator Sub-Agent                   │
│  (classifies severity, writes summary)      │
│                                             │
│  Tools:                                     │
│    create_ticket  ── writes .txt to disk     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
         output/tickets/<run_id>_ticket.txt
```

### Multi-Agent Pattern

Built with the [Strands Agents SDK](https://github.com/strands-agents/sdk-python) using the **Agents as Tools** pattern:

- **Orchestrator Agent** -- has a system prompt focused on investigating failures step-by-step. It reads the manifest, parses the logs, retrieves SQL source for failed models, then delegates to the sub-agent.
- **Ticket Creator Sub-Agent** -- a separate `Agent` instance with its own system prompt focused on severity classification and writing actionable summaries. Exposed as a `@tool` so the orchestrator can call it.

Both agents use **Claude Sonnet 4** via the Anthropic API.

### Ticket Contents

Each ticket file includes:

- **Severity** -- CRITICAL / HIGH / MEDIUM / LOW (classified by the LLM)
- **Summary** -- what failed, likely root cause, impact on downstream models, suggested fixes
- **Failed models** -- which dbt models failed
- **Error messages** -- extracted from the dbt JSON logs
- **SQL source** -- the SQL of the failing model(s)
- **Run metadata** -- command, exit code, timestamp

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- A [LocalStack auth token](https://app.localstack.cloud/) (free trial available)
- An [Anthropic API key](https://console.anthropic.com/) (required for the agent)

## Quick Start

1. **Clone and configure:**

   ```bash
   git clone <repo-url>
   cd ai-agentic-dbt-debugger
   cp .env.example .env
   # Edit .env and add your LOCALSTACK_AUTH_TOKEN and ANTHROPIC_API_KEY
   ```

2. **Build and start:**

   ```bash
   make build
   make up
   ```

   This starts the LocalStack Snowflake emulator, the dbt container, and the agent container. On startup, the init script (`localstack/init/ready.d/01_seed.py`) automatically creates the `BETTING` database, schemas, tables, and seed data.

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

6. **Test the agent** (requires `ANTHROPIC_API_KEY` in `.env`):

   ```bash
   # Introduce a failure (e.g., add a typo to dbt/models/conformed/fct_bet.sql)
   # then run with agent support:
   make dbt-run-agent

   # The agent will investigate and write a ticket to output/tickets/
   ```

   To manually invoke the agent against a past failed run:

   ```bash
   make agent-run RUN_ID=20260328T163421_380
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

### Agent

| Target | Description |
|---|---|
| `make dbt-run-agent` | Run dbt models; invoke agent on failure |
| `make dbt-test-agent` | Run dbt tests; invoke agent on failure |
| `make dbt-build-agent` | Run dbt build; invoke agent on failure |
| `make agent-run RUN_ID=<id>` | Manually invoke agent for a specific run ID |
| `make agent-shell` | Open an interactive shell in the agent container |

## Project Structure

```
.
├── Makefile                          # All commands
├── docker-compose.yml                # LocalStack + dbt + agent services
├── .env.example                      # Template for secrets
├── agent/
│   ├── Dockerfile                    # Python 3.12 + strands-agents
│   ├── pyproject.toml                # Agent package definition
│   └── agent/
│       ├── main.py                   # Entrypoint — accepts run_id, runs orchestrator
│       ├── orchestrator.py           # Orchestrator agent (system prompt + tools)
│       ├── agents/
│       │   └── ticket_agent.py       # Ticket Creator sub-agent (wrapped as @tool)
│       └── tools/
│           ├── read_dbt_manifest.py  # Read run manifest JSON
│           ├── read_dbt_logs.py      # Parse dbt JSON log lines for errors
│           ├── read_model_sql.py     # Read .sql source for a model name
│           └── create_ticket.py      # Write structured ticket .txt file
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
│   ├── dbt_with_agent.sh             # Host-side wrapper: dbt run + agent on failure
│   └── inspect_data.py               # Utility to introspect tables in LocalStack
├── output/
│   └── tickets/                      # Agent-generated failure tickets
└── logs/
    └── dbt/                          # Bind-mounted dbt logs (gitignored)
```

## run_dbt Wrapper

All `dbt-run`, `dbt-test`, and `dbt-build` commands go through the `run_dbt` wrapper script, which:

- Runs dbt with `--log-format json` for structured output
- Captures logs to `logs/dbt/runs/<run_id>.log`
- Writes a manifest to `logs/dbt/runs/<run_id>.manifest.json` with run metadata (exit code, success flag, timestamps)

This structured output is consumed by the agent when investigating failures.

## Troubleshooting

**`database "BETTING" does not exist`** -- The LocalStack init scripts may not have finished running. Wait a few seconds after `make up` and try again. The `inspect` script has built-in retry logic (5 attempts, 3s apart).

**`make clean` then `make up`** -- For a completely fresh start, this tears down all containers and volumes and rebuilds from scratch.

**Checking init script status:**

```bash
docker compose logs localstack | grep "seeded successfully"
```

You should see `BETTING database seeded successfully.` in the output.

**Agent fails with authentication error** -- Ensure `ANTHROPIC_API_KEY` is set in your `.env` file. The agent container reads this at startup. After updating `.env`, restart the agent: `docker compose restart agent`.

**Agent container not starting** -- Run `make build` to rebuild the agent image after any changes to `agent/`, then `make up`.
