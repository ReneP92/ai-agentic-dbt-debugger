"""Tool to read a Linear issue for a given dbt run ID."""

import json

from strands import tool

from agent.linear_client import LinearClientError, get_linear_client


@tool
def read_linear_issue(run_id: str) -> str:
    """Search Linear for the failure issue associated with a dbt run ID.

    Searches issue descriptions for the run_id string and returns the
    first matching issue's full details (title, description, priority,
    estimate, state, URL).

    Args:
        run_id: The dbt run identifier.  The tool searches Linear issue
                descriptions for this string to find the matching issue.

    Returns:
        A JSON string with the issue details on success, or an error
        message if no matching issue is found.
    """
    try:
        client = get_linear_client()

        issues = client.search_issues(run_id, first=3)

        # Find the issue whose description contains the exact run_id
        match = None
        for issue in issues:
            desc = issue.get("description", "") or ""
            if run_id in desc:
                match = issue
                break

        if not match:
            return json.dumps({
                "error": f"No Linear issue found containing run_id '{run_id}'",
            })

        return json.dumps({
            "issue_id": match.get("id", ""),
            "identifier": match.get("identifier", ""),
            "title": match.get("title", ""),
            "description": match.get("description", ""),
            "priority": match.get("priority"),
            "url": match.get("url", ""),
            "state": match.get("state", {}).get("name", ""),
        })

    except LinearClientError as exc:
        return json.dumps({
            "error": str(exc),
        })
