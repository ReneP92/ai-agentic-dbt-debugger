"""Tool to add a comment to a Linear issue (e.g. linking a PR)."""

import json

from strands import tool

from agent.linear_client import LinearClientError, get_linear_client


@tool
def comment_linear_issue(issue_id: str, body: str) -> str:
    """Add a comment to a Linear issue.

    Typically used after creating a pull request to link it back to the
    Linear issue so stakeholders can track the fix.

    Args:
        issue_id: The Linear issue UUID (returned by create_linear_issue
                  or read_linear_issue as the ``issue_id`` field).
        body: Markdown-formatted comment body.  For PR linking, include
              the PR URL and a brief description of the fix.

    Returns:
        A JSON string confirming the comment was created, or an error
        message on failure.
    """
    try:
        client = get_linear_client()
        comment = client.add_comment(issue_id=issue_id, body=body)

        return json.dumps({
            "status": "created",
            "comment_id": comment.get("id", ""),
        })

    except LinearClientError as exc:
        return json.dumps({
            "status": "error",
            "error": str(exc),
        })
