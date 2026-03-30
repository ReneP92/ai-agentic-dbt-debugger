"""Tool to create a GitHub pull request using the gh CLI."""

import json
import os
import subprocess
from pathlib import Path

from strands import tool

WORKSPACE = Path("/usr/app/workspace")


@tool
def create_pull_request(
    branch_name: str,
    title: str,
    body: str,
    base_branch: str = "main",
) -> str:
    """Create a GitHub pull request for the fix branch using the ``gh`` CLI.

    Requires the ``GITHUB_AUTH_TOKEN`` environment variable to be set for
    authentication.  The PR is created from the workspace directory where
    the repository was cloned.

    Args:
        branch_name: The head branch containing the fix (e.g.
                     ``fix/dbt-<run_id>``).
        title: A short title for the pull request.
        body: The PR body/description.  Should include the ticket summary
              and details about what was fixed.
        base_branch: The branch to merge into (default: ``main``).

    Returns:
        A JSON string with ``pr_url`` and ``pr_number`` fields, or an
        error message if PR creation fails.
    """
    token = os.environ.get("GITHUB_AUTH_TOKEN", "")
    if not token:
        return json.dumps({"error": "GITHUB_AUTH_TOKEN environment variable is not set"})

    if not WORKSPACE.exists():
        return json.dumps({"error": "Workspace does not exist — clone the repo first."})

    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": "/root",
        "GITHUB_TOKEN": token,  # gh CLI expects GITHUB_TOKEN
    }

    result = subprocess.run(
        [
            "gh", "pr", "create",
            "--base", base_branch,
            "--head", branch_name,
            "--title", title,
            "--body", body,
        ],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE),
        env=env,
    )

    if result.returncode != 0:
        return json.dumps({
            "error": f"gh pr create failed: {result.stderr.strip()}",
            "stdout": result.stdout.strip(),
        })

    # gh pr create prints the PR URL on stdout
    pr_url = result.stdout.strip()

    # Try to extract the PR number from the URL
    pr_number = ""
    if "/pull/" in pr_url:
        pr_number = pr_url.rsplit("/pull/", 1)[-1].strip("/")

    return json.dumps({
        "pr_url": pr_url,
        "pr_number": pr_number,
    })
