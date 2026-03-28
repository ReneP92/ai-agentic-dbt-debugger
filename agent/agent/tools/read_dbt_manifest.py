"""Tool to read the manifest JSON produced by run_dbt.sh for a given run."""

import json
from pathlib import Path

from strands import tool

LOGS_BASE = Path("/usr/app/logs/dbt/runs")


@tool
def read_dbt_manifest(run_id: str) -> str:
    """Read the dbt run manifest for a given run ID.

    The manifest contains structured metadata about a dbt run including
    the run_id, command executed, exit_code, log_file path, started_at
    timestamp, and whether the run was successful.

    Args:
        run_id: The unique identifier of the dbt run (e.g. '20260328T163421_380').

    Returns:
        A JSON string with the manifest contents, or an error message if not found.
    """
    manifest_path = LOGS_BASE / f"{run_id}.manifest.json"

    if not manifest_path.exists():
        return json.dumps({"error": f"Manifest not found: {manifest_path}"})

    return manifest_path.read_text()
