"""Tool to clone the GitHub repository and create a fix branch."""

import json
import os
import shutil
import subprocess
from pathlib import Path

from strands import tool

WORKSPACE = Path("/usr/app/workspace")


@tool
def clone_repo(run_id: str) -> str:
    """Clone the GitHub repository and create a fix branch for a dbt run failure.

    Performs a shallow clone of the repository's main branch into a local
    workspace directory, then creates and checks out a new branch named
    ``fix/dbt-<run_id>`` for the automated fix.

    Requires environment variables:
    - GITHUB_REPO_URL: The HTTPS URL of the repository.
    - GITHUB_TOKEN: A GitHub PAT with push access.

    Args:
        run_id: The dbt run identifier, used to name the fix branch.

    Returns:
        A JSON string with ``workspace_path`` and ``branch_name``, or an
        error message if cloning fails.
    """
    repo_url = os.environ.get("GITHUB_REPO_URL", "")
    token = os.environ.get("GITHUB_TOKEN", "")

    if not repo_url:
        return json.dumps({"error": "GITHUB_REPO_URL environment variable is not set"})
    if not token:
        return json.dumps({"error": "GITHUB_TOKEN environment variable is not set"})

    # Inject token into the HTTPS URL for authentication
    # https://github.com/org/repo.git -> https://<token>@github.com/org/repo.git
    if repo_url.startswith("https://"):
        authed_url = repo_url.replace("https://", f"https://{token}@", 1)
    else:
        authed_url = repo_url

    # Clean up any previous workspace
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)

    branch_name = f"fix/dbt-{run_id}"

    # Shallow clone the main branch
    result = subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", "main", authed_url, str(WORKSPACE)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return json.dumps({
            "error": f"git clone failed: {result.stderr.strip()}",
        })

    # Create and checkout the fix branch
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE),
    )

    if result.returncode != 0:
        return json.dumps({
            "error": f"git checkout -b failed: {result.stderr.strip()}",
        })

    return json.dumps({
        "workspace_path": str(WORKSPACE),
        "branch_name": branch_name,
    })
