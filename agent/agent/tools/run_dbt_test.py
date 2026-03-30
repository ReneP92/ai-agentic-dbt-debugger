"""Tool to run dbt test against a specific model for fix verification."""

import json
import subprocess
from pathlib import Path

from strands import tool

WORKSPACE = Path("/usr/app/workspace")


@tool
def run_dbt_test(model_name: str) -> str:
    """Run dbt test for a specific model to verify a fix.

    Executes ``dbt deps && dbt test --select <model_name>`` inside the
    cloned workspace's dbt project directory.  The dbt profile is expected
    to be in the workspace at ``dbt/profiles.yml`` (set via
    ``DBT_PROFILES_DIR`` environment variable).

    This tool should be called after writing a fix to verify the fix
    resolves the original failure before committing.

    Args:
        model_name: The dbt model name to test (e.g. ``fct_bet``).

    Returns:
        A JSON string with ``success`` (bool), ``return_code``, ``stdout``,
        and ``stderr`` fields.
    """
    dbt_project_dir = WORKSPACE / "dbt"

    if not dbt_project_dir.exists():
        return json.dumps({
            "error": f"dbt project directory not found: {dbt_project_dir}",
        })

    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": "/root",
        "DBT_PROFILES_DIR": str(dbt_project_dir),
    }

    # Run dbt deps first (needed for dbt_utils)
    deps_result = subprocess.run(
        ["dbt", "deps"],
        capture_output=True,
        text=True,
        cwd=str(dbt_project_dir),
        env=env,
        timeout=120,
    )

    if deps_result.returncode != 0:
        return json.dumps({
            "success": False,
            "return_code": deps_result.returncode,
            "stdout": deps_result.stdout[-2000:] if len(deps_result.stdout) > 2000 else deps_result.stdout,
            "stderr": deps_result.stderr[-2000:] if len(deps_result.stderr) > 2000 else deps_result.stderr,
            "phase": "dbt deps",
        })

    # Run dbt test for the specific model
    result = subprocess.run(
        ["dbt", "test", "--select", model_name],
        capture_output=True,
        text=True,
        cwd=str(dbt_project_dir),
        env=env,
        timeout=120,
    )

    return json.dumps({
        "success": result.returncode == 0,
        "return_code": result.returncode,
        "stdout": result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout,
        "stderr": result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr,
        "phase": "dbt test",
    })
