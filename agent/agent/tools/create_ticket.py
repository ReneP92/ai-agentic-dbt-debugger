"""Tool to write a structured failure ticket to disk."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from strands import tool

TICKETS_DIR = Path("/usr/app/output/tickets")


@tool
def create_ticket(
    run_id: str,
    title: str,
    severity: str,
    summary: str,
    failed_models: list[str],
    error_messages: list[str],
    sql_snippets: list[str],
    command: str,
    exit_code: int,
    started_at: Optional[str] = None,
) -> str:
    """Create a structured failure ticket as a .txt file.

    Writes a human-readable ticket file to the output/tickets/ directory
    containing all relevant information about the dbt run failure.

    Args:
        run_id: The dbt run identifier (used in the filename).
        title: A short descriptive title for the failure.
        severity: One of CRITICAL, HIGH, MEDIUM, LOW.
        summary: An LLM-generated summary explaining what went wrong and potential fixes.
        failed_models: List of dbt model names that failed.
        error_messages: List of error messages extracted from the dbt logs.
        sql_snippets: List of SQL source snippets from the failing models.
        command: The dbt command that was run (e.g. 'dbt run').
        exit_code: The process exit code.
        started_at: ISO-8601 timestamp of when the run started (optional).

    Returns:
        A confirmation message with the path to the created ticket file.
    """
    TICKETS_DIR.mkdir(parents=True, exist_ok=True)

    ticket_path = TICKETS_DIR / f"{run_id}_ticket.txt"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    models_block = "\n".join(f"  - {m}" for m in failed_models) if failed_models else "  (none identified)"
    errors_block = "\n\n".join(error_messages) if error_messages else "(no error messages captured)"
    sql_block = "\n\n---\n\n".join(sql_snippets) if sql_snippets else "(no SQL captured)"

    ticket = f"""\
============================================
DBT FAILURE TICKET
============================================
Ticket ID:     {run_id}
Created:       {now}
Severity:      {severity.upper()}
Title:         {title}

SUMMARY
-------
{summary}

FAILED MODELS
-------------
{models_block}

ERROR DETAILS
-------------
{errors_block}

SQL (source)
------------
{sql_block}

RUN METADATA
------------
Command:       {command}
Exit Code:     {exit_code}
Started At:    {started_at or "unknown"}
============================================
"""

    ticket_path.write_text(ticket)

    return json.dumps(
        {
            "status": "created",
            "ticket_path": str(ticket_path),
            "ticket_id": run_id,
        }
    )
