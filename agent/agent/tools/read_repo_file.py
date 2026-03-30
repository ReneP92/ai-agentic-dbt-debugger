"""Tool to read a file from the cloned repository workspace."""

import json
from pathlib import Path

from strands import tool

WORKSPACE = Path("/usr/app/workspace")
ALLOWED_PREFIX = "dbt/models/"


@tool
def read_repo_file(file_path: str) -> str:
    """Read a file from the cloned repository workspace.

    For safety, only files under ``dbt/models/`` can be read.  The path
    must be relative to the workspace root.

    Args:
        file_path: Path relative to the workspace root (e.g.
                   ``dbt/models/conformed/fct_bet.sql``).

    Returns:
        A JSON string with ``file_path`` and ``content`` fields, or an
        error message if the file is not found or the path is disallowed.
    """
    if not file_path.startswith(ALLOWED_PREFIX):
        return json.dumps({
            "error": (
                f"Access denied: only files under '{ALLOWED_PREFIX}' can be read. "
                f"Got: '{file_path}'"
            ),
        })

    full_path = WORKSPACE / file_path

    if not full_path.exists():
        return json.dumps({"error": f"File not found: {full_path}"})

    # Guard against path traversal
    try:
        full_path.resolve().relative_to(WORKSPACE.resolve())
    except ValueError:
        return json.dumps({"error": "Path traversal detected — access denied."})

    return json.dumps({
        "file_path": file_path,
        "content": full_path.read_text(),
    })
