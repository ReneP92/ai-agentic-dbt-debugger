"""Tool to read and parse dbt JSON log lines for a given run."""

import json
from pathlib import Path

from strands import tool

LOGS_BASE = Path("/usr/app/logs/dbt/runs")


@tool
def read_dbt_logs(run_id: str) -> str:
    """Read the dbt JSON log file for a given run ID and extract error/warning events.

    Parses the JSON-lines log file produced by `dbt --log-format json` and
    returns only the entries with level ERROR or WARN, plus any entries that
    contain node (model) information.  This keeps the context focused on
    what went wrong.

    Args:
        run_id: The unique identifier of the dbt run (e.g. '20260328T163421_380').

    Returns:
        A JSON string containing a list of relevant log entries with fields:
        level, message, node_id (if present), timestamp, and the raw log_line.
        Returns an error message if the log file is not found.
    """
    log_path = LOGS_BASE / f"{run_id}.log"

    if not log_path.exists():
        return json.dumps({"error": f"Log file not found: {log_path}"})

    relevant_entries = []

    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            # Some lines may be plain text (e.g. dbt's banner); skip them
            continue

        level = entry.get("info", {}).get("level", "").upper()
        msg = entry.get("info", {}).get("msg", "")
        ts = entry.get("info", {}).get("ts", "")

        # Extract node info if present (tells us which model is involved)
        data = entry.get("data", {}) or entry.get("info", {}).get("data", {}) or {}
        node_info = data.get("node_info", {})
        node_id = node_info.get("unique_id", "") if node_info else ""

        # Keep errors, warnings, and any line that references a node
        if level in ("ERROR", "WARN") or node_id:
            relevant_entries.append(
                {
                    "level": level,
                    "message": msg,
                    "node_id": node_id,
                    "timestamp": ts,
                }
            )

    return json.dumps(relevant_entries, indent=2)
