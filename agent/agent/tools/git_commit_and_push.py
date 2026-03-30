"""Tool to commit changes and push the fix branch to the remote."""

import json
import subprocess
from pathlib import Path

from strands import tool

WORKSPACE = Path("/usr/app/workspace")


@tool
def git_commit_and_push(commit_message: str, branch_name: str) -> str:
    """Stage all changes, commit, and push the fix branch to the remote.

    Runs ``git add -A``, ``git commit``, and ``git push origin <branch>``
    inside the cloned workspace.  Authentication is handled via the token
    already embedded in the remote URL during ``clone_repo``.

    Args:
        commit_message: The commit message describing the fix.
        branch_name: The branch name to push (e.g. ``fix/dbt-<run_id>``).

    Returns:
        A JSON string with ``success``, ``branch_name``, and ``commit_sha``
        fields, or an error message if any git operation fails.
    """
    if not WORKSPACE.exists():
        return json.dumps({"error": "Workspace does not exist — clone the repo first."})

    # Stage all changes
    result = subprocess.run(
        ["git", "add", "-A"],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE),
    )
    if result.returncode != 0:
        return json.dumps({"error": f"git add failed: {result.stderr.strip()}"})

    # Check if there are changes to commit
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE),
    )
    if not status.stdout.strip():
        return json.dumps({"error": "No changes to commit."})

    # Commit
    result = subprocess.run(
        ["git", "commit", "-m", commit_message],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE),
    )
    if result.returncode != 0:
        return json.dumps({"error": f"git commit failed: {result.stderr.strip()}"})

    # Get the commit SHA
    sha_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE),
    )
    commit_sha = sha_result.stdout.strip()

    # Push to remote
    result = subprocess.run(
        ["git", "push", "origin", branch_name],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE),
    )
    if result.returncode != 0:
        return json.dumps({
            "error": f"git push failed: {result.stderr.strip()}",
            "commit_sha": commit_sha,
        })

    return json.dumps({
        "success": True,
        "branch_name": branch_name,
        "commit_sha": commit_sha,
    })
