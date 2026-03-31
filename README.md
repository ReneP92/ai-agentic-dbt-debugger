<img src="./assets/corgi.png" alt="icon" width="80" />

# ai-agentic-dbt-debugger

A self-contained dbt project running against a [LocalStack Snowflake](https://docs.localstack.cloud/snowflake/) emulator, with an AI agent system that automatically investigates dbt pipeline failures, creates Linear issues with structured failure details, and opens GitHub pull requests with automated fixes. Includes a lightweight live monitoring dashboard for watching agent execution in real time — LLM calls, tool usage, token counts, and cost estimates streamed via WebSocket.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  Docker Compose (dbt-net bridge network)                                                                                                    │
│                                                                                                                                             │
│                                                                                                                                             │
│   ┌─────────────────────┐         ┌─────────────────────┐        ┌───────────────┐        ┌─────────────────────┐        ┌────────────────┐  │
│   │  localstack         │         │  dbt                │  (rw)  │               │  (ro)  │  agent              │        │  code-env      │  │
│   │                     │         │                     │───────>│   logs/dbt/   │<───────│                     │        │                │  │
│   │  Snowflake emu      │◄────────│  Python 3.12        │        │   runs/       │        │  Python 3.12        │        │  Python 3.12   │  │
│   │  Port 4566          │         │  dbt-snowflake 1.9.1│        │               │        │  Strands Agents     │        │  git + gh CLI  │  │
│   │                     │         │                     │        └───────────────┘        │  Claude Sonnet 4    │        │  dbt-snowflake │  │
│   │                     │         │                     │                                 │                     │        │  Strands Agents│  │
│   └─────────────────────┘         └─────────────────────┘                                 └──────────┬──────────┘        └───────┬────────┘  │
│          ▲                                                                                           │                          │           │
│          │                                                                                           │  WS push                 │  WS push  │
│          │                                                                                           │                          │           │
│          │                         reads Linear issues, runs dbt test                                │                          │           │
│          └─────────────────────────clones repo, pushes fix, opens PR─────────────────────────────────────────────────────────────┘           │
│                                                                                                      │                          │           │
│                                                                                                      ▼                          ▼           │
│                                                                                ┌─────────────────────────────────────────────────────────┐   │
│                                                                                │  monitor (:3001)                                       │   │
│                                                                                │                                                        │   │
│                                                                                │  FastAPI  +  WebSocket  +  SQLite                       │   │
│                                                                                │  Vanilla HTML/JS/CSS dashboard                          │   │
│                                                                                └─────────────────────────────────────────────────────────┘   │
│                                                                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**LocalStack Snowflake** emulates a Snowflake warehouse locally so no cloud account is needed. The **dbt** container runs as a long-lived sidecar and all commands are issued via `docker compose exec`. The **agent** container runs the AI debugging agent -- it reads dbt logs and model SQL (read-only) and creates Linear issues in the Data Alerts project with structured failure details. The **code-env** container runs the Code-Fix agent -- it reads the Linear issue, clones the repo, fixes the dbt code, verifies with `dbt test`, and opens a GitHub PR. The **monitor** container provides a real-time browser dashboard for watching agent execution.

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

The agent system reacts to dbt run failures. When a dbt command exits non-zero, a wrapper script invokes the AI agent to investigate the failure and create a Linear issue.

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
│  (classifies severity, estimates effort,    │
│   writes summary)                           │
│                                             │
│  Tools:                                     │
│    create_linear_issue ── Linear API         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
         Linear Issue (Data Alerts project)
         e.g. REN-42
```

### Multi-Agent Pattern

Built with the [Strands Agents SDK](https://github.com/strands-agents/sdk-python) using the **Agents as Tools** pattern:

- **Orchestrator Agent** -- has a system prompt focused on investigating failures step-by-step. It reads the manifest, parses the logs, retrieves SQL source for failed models, then delegates to the sub-agent.
- **Ticket Creator Sub-Agent** -- a separate `Agent` instance with its own system prompt focused on severity classification and writing actionable summaries. Exposed as a `@tool` so the orchestrator can call it.
- **Code-Fix Sub-Agent** -- a separate `Agent` instance that clones the repo, reads the Linear issue, fixes dbt model files, verifies with `dbt test`, and opens a GitHub PR. Exposed as a `@tool` so its orchestrator can call it.

All agents use **Claude Sonnet 4** via the Anthropic API.

### Code-Fix Agent

After the Linear issue is created, the code-fix agent attempts an automated repair:

```
Linear Issue (Data Alerts project)
      │
      ▼
┌─────────────────────────────────────────────┐
│  Code-Fix Orchestrator                      │
│  (delegates to code-fix sub-agent)          │
│                                             │
│  Tools:                                     │
│    code_fix_agent  ── sub-agent (below)      │
└──────────────────┬──────────────────────────┘
                   │  delegates with run_id
                   ▼
┌─────────────────────────────────────────────┐
│  Code-Fix Sub-Agent                         │
│  (clones repo, reads Linear issue, fixes    │
│   code, verifies, commits, opens PR)        │
│                                             │
│  Tools:                                     │
│    clone_repo            ── git clone+branch │
│    read_linear_issue     ── read from Linear │
│    read_repo_file        ── read dbt SQL/YAML│
│    write_repo_file       ── write fixed files│
│    run_dbt_test          ── verify fix works │
│    git_commit_and_push   ── commit + push    │
│    create_pull_request   ── gh pr create     │
│    query_snowflake       ── inspect data     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
         GitHub Pull Request
         (branch: fix/dbt-<run_id>)
```

**Retry logic:** If `dbt test` fails after writing a fix, the agent reads the error output, adjusts the fix, and retries (up to 3 attempts). If all retries are exhausted, the agent exits with a non-zero code without pushing any code.

**Safety constraints:** The code-fix agent can only modify files under `dbt/models/` -- it cannot touch infrastructure, agent code, or anything outside the dbt models directory.

### Live Agent Monitor

Agent execution is observable in real time through a lightweight browser-based dashboard. Both the ticket agent and code-fix agent push events over WebSocket to the monitor server, which stores them in SQLite and broadcasts them to any connected browser clients.

The dashboard shows:

- **Run lifecycle** -- start/end with success/failure status and total duration
- **LLM calls** -- model invocation start/end with stop reasons
- **Tool calls** -- tool name, inputs, outputs, duration, and success/failure status (collapsible)
- **Sub-agent delegation** -- when the orchestrator delegates to a sub-agent, with nested indentation
- **Streaming tokens** -- real-time text and reasoning/thinking output from the LLM
- **Metrics summary** -- input/output/cache token counts, latency, cycle count, estimated cost, and per-tool stats
- **Historical runs** -- browse past runs from a dropdown, with full event replay

**Access the UI:**

```bash
make monitor-open    # Opens http://localhost:3001
```

No credentials required. The monitor starts automatically with `make up`.

**How it works:**

1. Both agent entrypoints (`main.py`, `code_fix_main.py`) call `setup_monitor()` at startup
2. This creates a `MonitorHookProvider` (Strands lifecycle hooks) and a `MonitorCallbackHandler` (streaming tokens)
3. Events are pushed over WebSocket to the monitor server at `ws://monitor:8765/ws/push`
4. The monitor server stores events in SQLite and broadcasts them to browser clients via `ws://monitor:8765/ws/live`
5. The browser dashboard renders events as they arrive with auto-scroll

If `MONITOR_WS_URL` is not set, monitoring is silently skipped and the agents work as before.

### Linear Issue Contents

Each Linear issue in the Data Alerts project includes:

- **Priority** -- Urgent / High / Medium / Low (mapped from severity classification)
- **Estimate** -- T-shirt size (XS/S/M/L/XL) mapped to Fibonacci points (1/2/3/5/8)
- **Summary** -- what failed, likely root cause, impact on downstream models, suggested fixes
- **Failed models** -- which dbt models failed
- **Error messages** -- extracted from the dbt JSON logs
- **SQL source** -- the SQL of the failing model(s)
- **Run metadata** -- run ID, command, exit code, timestamp

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- A [LocalStack auth token](https://app.localstack.cloud/) (free trial available)
- An [Anthropic API key](https://console.anthropic.com/) (required for the agent)
- A [GitHub PAT](https://github.com/settings/tokens) with repo push + PR permissions (required for code-fix agent)
- A [Linear API key](https://linear.app/settings/api) (personal API key for issue management)

## Quick Start

1. **Clone and configure:**

   ```bash
   git clone <repo-url>
   cd ai-agentic-dbt-debugger
    cp .env.example .env
     # Edit .env and add your LOCALSTACK_AUTH_TOKEN, ANTHROPIC_API_KEY,
      # GITHUB_AUTH_TOKEN, GITHUB_REPO_URL, and LINEAR_AUTH_TOKEN
   ```

2. **Build and start:**

   ```bash
   make build
   make up
   ```

   This starts the LocalStack Snowflake emulator, the dbt container, the agent container, the code-env container, and the live agent monitor. On startup, the init script (`localstack/init/ready.d/01_seed.py`) automatically creates the `BETTING` database, schemas, tables, and seed data.

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

   # The agent will:
   # 1. Investigate and create a Linear issue in the Data Alerts project
   # 2. Attempt an automated fix and open a GitHub PR (requires GITHUB_AUTH_TOKEN)
   ```

   To manually invoke individual agents against a past failed run:

   ```bash
   make agent-run RUN_ID=20260328T163421_380    # Ticket agent only
   make code-fix RUN_ID=20260328T163421_380      # Code-fix agent only
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

### Code-Fix

| Target | Description |
|---|---|
| `make code-fix RUN_ID=<id>` | Manually invoke code-fix agent for a specific run ID |
| `make code-env-shell` | Open an interactive shell in the code-env container |

### Observability

| Target | Description |
|---|---|
| `make monitor-open` | Open the Agent Monitor UI in your browser (http://localhost:3001) |
| `make monitor-logs` | Follow logs for the monitor service |

## Project Structure

```
.
├── Makefile                          # All commands
├── docker-compose.yml                # LocalStack + dbt + agent + code-env + monitor services
├── .env.example                      # Template for secrets
├── agent/
│   ├── Dockerfile                    # Python 3.12 + strands-agents
│   ├── pyproject.toml                # Agent package definition
│   └── agent/
│       ├── main.py                   # Entrypoint — accepts run_id, runs orchestrator
│       ├── orchestrator.py           # Orchestrator agent (system prompt + tools)
│       ├── code_fix_main.py          # Entrypoint — accepts run_id, runs code-fix agent
│       ├── linear_client.py          # Linear GraphQL API client (issue CRUD, comments)
│       ├── monitor.py                # Live monitor — WebSocket hooks + streaming handler
│       ├── agents/
│       │   ├── ticket_agent.py       # Ticket Creator sub-agent (wrapped as @tool)
│       │   └── code_fix_agent.py     # Code-Fix sub-agent (wrapped as @tool)
│       └── tools/
│           ├── read_dbt_manifest.py  # Read run manifest JSON
│           ├── read_dbt_logs.py      # Parse dbt JSON log lines for errors
│           ├── read_model_sql.py     # Read .sql source for a model name
│           ├── create_linear_issue.py # Create Linear issue for dbt failure
│           ├── read_linear_issue.py  # Read Linear issue by run_id search
│           ├── clone_repo.py         # Clone repo + create fix branch
│           ├── read_repo_file.py     # Read file from cloned workspace
│           ├── write_repo_file.py    # Write file in cloned workspace
│           ├── run_dbt_test.py       # Run dbt test for verification
│           ├── git_commit_and_push.py # Commit + push fix branch
│           ├── create_pull_request.py # Create GitHub PR via gh CLI
│           └── query_snowflake.py    # Read-only SQL queries against Snowflake
├── monitor/
│   ├── Dockerfile                    # Python 3.12 + FastAPI + uvicorn
│   ├── requirements.txt             # Server dependencies
│   ├── server.py                    # FastAPI app with WebSocket + REST endpoints
│   ├── db.py                        # SQLite storage layer (WAL mode)
│   ├── schema.sql                   # Database schema (runs + events tables)
│   └── static/
│       ├── index.html               # Dashboard HTML structure
│       ├── style.css                # Dark-themed styling
│       └── app.js                   # Dashboard JavaScript (WebSocket + rendering)
├── code-env/
│   └── Dockerfile                    # Python 3.12 + git + gh CLI + dbt + agent
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
│   ├── dbt_with_agent.sh             # Host-side wrapper: dbt run + agent + code-fix
│   └── inspect_data.py               # Utility to introspect tables in LocalStack
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

**Code-fix agent fails to push/create PR** -- Ensure `GITHUB_AUTH_TOKEN` and `GITHUB_REPO_URL` are set in your `.env` file. The token needs repo push and PR creation permissions. After updating `.env`, restart the code-env container: `docker compose restart code-env`.

**Linear issue creation fails** -- Ensure `LINEAR_AUTH_TOKEN` is set in your `.env` file with a valid Linear personal API key. The agent needs access to a team with key `REN` and a project named `Data Alerts`. After updating `.env`, restart the agent: `docker compose restart agent code-env`.

**Agent container not starting** -- Run `make build` to rebuild the agent image after any changes to `agent/`, then `make up`.
