#!/bin/bash
# run_dbt.sh — wrapper around dbt that captures structured logs for the LLM agent.
#
# Usage (inside the dbt container):
#   run_dbt run
#   run_dbt run --select standardised
#   run_dbt test
#   run_dbt build
#
# Every invocation writes two files to $LOG_DIR:
#   <run_id>.log           — raw dbt output (JSON log lines from --log-format json)
#   <run_id>.manifest.json — structured metadata for the agent to scan

set -euo pipefail

COMMAND="${*:-run}"
RUN_ID="$(date +%Y%m%dT%H%M%S)_$$"
LOG_DIR="/usr/app/dbt/logs/runs"
LOG_FILE="${LOG_DIR}/${RUN_ID}.log"
MANIFEST_FILE="${LOG_DIR}/${RUN_ID}.manifest.json"

mkdir -p "$LOG_DIR"

echo "[run_dbt] Starting: dbt ${COMMAND}"
echo "[run_dbt] Run ID:   ${RUN_ID}"
echo "[run_dbt] Log:      ${LOG_FILE}"

# Capture stdout/stderr; exit code is captured separately so the script doesn't
# abort on dbt failure (we want to write the manifest even on failure).
set +e
# shellcheck disable=SC2086
dbt ${COMMAND} --log-format json 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE=$?
set -e

cat > "$MANIFEST_FILE" <<JSON
{
  "run_id":    "${RUN_ID}",
  "command":   "dbt ${COMMAND}",
  "exit_code": ${EXIT_CODE},
  "log_file":  "${LOG_FILE}",
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "success":   $([ "$EXIT_CODE" -eq 0 ] && echo true || echo false)
}
JSON

echo "[run_dbt] Finished (exit ${EXIT_CODE})"
echo "[run_dbt] Manifest: ${MANIFEST_FILE}"

exit "$EXIT_CODE"
