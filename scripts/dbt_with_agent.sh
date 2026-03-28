#!/bin/bash
# dbt_with_agent.sh — run dbt and invoke the debugger agent on failure.
#
# Usage:
#   ./scripts/dbt_with_agent.sh run
#   ./scripts/dbt_with_agent.sh test
#   ./scripts/dbt_with_agent.sh build
#
# Runs `dbt deps && run_dbt <command>` inside the dbt container.
# If dbt exits non-zero, extracts the run_id from the latest manifest
# and invokes the agent to investigate and create a ticket.

set -uo pipefail

COMMAND="${1:-run}"

echo "=== Running: dbt ${COMMAND} ==="
docker compose exec dbt sh -c "dbt deps && run_dbt ${COMMAND}"
DBT_EXIT=$?

if [ "$DBT_EXIT" -eq 0 ]; then
    echo "=== dbt ${COMMAND} succeeded ==="
    exit 0
fi

echo "=== dbt ${COMMAND} failed (exit ${DBT_EXIT}) — invoking agent ==="

# Find the most recent manifest file to get the run_id.
# Manifests are written to logs/dbt/runs/<run_id>.manifest.json by run_dbt.sh.
LATEST_MANIFEST=$(ls -t logs/dbt/runs/*.manifest.json 2>/dev/null | head -1)

if [ -z "$LATEST_MANIFEST" ]; then
    echo "[ERROR] No manifest file found in logs/dbt/runs/ — cannot invoke agent."
    exit "$DBT_EXIT"
fi

# Extract run_id from filename: logs/dbt/runs/<run_id>.manifest.json
RUN_ID=$(basename "$LATEST_MANIFEST" .manifest.json)

echo "=== Agent investigating run_id: ${RUN_ID} ==="
docker compose exec agent python -m agent.main "$RUN_ID"
AGENT_EXIT=$?

if [ "$AGENT_EXIT" -ne 0 ]; then
    echo "[WARN] Agent exited with code ${AGENT_EXIT}"
fi

echo "=== Done. Check output/tickets/ for the failure ticket. ==="
exit "$DBT_EXIT"
