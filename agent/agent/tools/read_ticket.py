"""Tool to read a failure ticket produced by the ticket agent."""

import json
from pathlib import Path

from strands import tool

TICKETS_DIR = Path("/usr/app/output/tickets")


@tool
def read_ticket(run_id: str) -> str:
    """Read the failure ticket file for a given dbt run ID.

    The ticket was previously created by the Ticket Creator sub-agent and
    contains the severity classification, failure summary, error messages,
    failed model names, and SQL source code.

    Args:
        run_id: The dbt run identifier (matches the ticket filename pattern
                ``<run_id>_ticket.txt``).

    Returns:
        A JSON string with ``ticket_path`` and ``content`` fields, or an
        error message if the ticket file is not found.
    """
    ticket_path = TICKETS_DIR / f"{run_id}_ticket.txt"

    if not ticket_path.exists():
        return json.dumps({
            "error": f"Ticket not found: {ticket_path}",
        })

    return json.dumps({
        "ticket_path": str(ticket_path),
        "content": ticket_path.read_text(),
    })
