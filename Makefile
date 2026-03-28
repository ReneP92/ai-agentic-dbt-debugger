.PHONY: help build up down restart logs ps clean \
        dbt-debug dbt-run dbt-test dbt-build dbt-shell dbt-deps inspect \
        dbt-run-agent dbt-test-agent dbt-build-agent agent-shell agent-run

# Default target
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Infrastructure"
	@echo "  build       Build all Docker images"
	@echo "  up          Start all services (detached)"
	@echo "  down        Stop and remove containers"
	@echo "  restart     Restart all services"
	@echo "  logs        Follow logs for all services"
	@echo "  ps          Show container status"
	@echo "  clean       Remove containers, volumes, and images"
	@echo ""
	@echo "dbt"
	@echo "  dbt-debug   Verify dbt can connect to LocalStack Snowflake"
	@echo "  dbt-deps    Install dbt packages (dbt deps)"
	@echo "  dbt-run     Run all dbt models (via run_dbt wrapper)"
	@echo "  dbt-test    Run all dbt tests (via run_dbt wrapper)"
	@echo "  dbt-build   Run dbt build — models + tests in one pass"
	@echo "  dbt-shell   Open an interactive shell in the dbt container"
	@echo "  inspect     Print schema + 10 random rows for every table in LocalStack"
	@echo ""
	@echo "Agent"
	@echo "  dbt-run-agent   Run dbt models; invoke agent on failure"
	@echo "  dbt-test-agent  Run dbt tests; invoke agent on failure"
	@echo "  dbt-build-agent Run dbt build; invoke agent on failure"
	@echo "  agent-run       Manually invoke agent for a run ID (make agent-run RUN_ID=...)"
	@echo "  agent-shell     Open an interactive shell in the agent container"

# ── Infrastructure ────────────────────────────────────────────────────────────

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	docker compose down --volumes --rmi local

# ── dbt ───────────────────────────────────────────────────────────────────────

dbt-debug:
	docker compose exec dbt dbt debug

dbt-deps:
	docker compose exec dbt dbt deps

dbt-run:
	docker compose exec dbt sh -c "dbt deps && run_dbt run"

dbt-test:
	docker compose exec dbt sh -c "dbt deps && run_dbt test"

dbt-build:
	docker compose exec dbt sh -c "dbt deps && run_dbt build"

dbt-shell:
	docker compose exec dbt bash

inspect:
	docker compose exec -T dbt python - < scripts/inspect_data.py

# ── Agent ─────────────────────────────────────────────────────────────────────

dbt-run-agent:
	./scripts/dbt_with_agent.sh run

dbt-test-agent:
	./scripts/dbt_with_agent.sh test

dbt-build-agent:
	./scripts/dbt_with_agent.sh build

agent-run:
	@test -n "$(RUN_ID)" || (echo "Usage: make agent-run RUN_ID=<run_id>" && exit 1)
	docker compose exec agent python -m agent.main $(RUN_ID)

agent-shell:
	docker compose exec agent bash
