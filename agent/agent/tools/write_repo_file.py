"""Tool to write a file in the cloned repository workspace."""

import json
from pathlib import Path

from strands import tool

WORKSPACE = Path("/usr/app/workspace")
ALLOWED_PREFIXES = ("dbt/models/",)


@tool
def write_repo_file(file_path: str, content: str) -> str:
    """Write content to a file in the cloned repository workspace.

    For safety, only files under ``dbt/models/`` can be written.  The path
    must be relative to the workspace root.  Parent directories are created
    automatically if they do not exist.

    Args:
        file_path: Path relative to the workspace root (e.g.
                   ``dbt/models/conformed/fct_bet.sql``).
        content: The full file content to write.

    Returns:
        A JSON string confirming the write, or an error message if the
        path is disallowed.
    """
    allowed = any(file_path.startswith(prefix) for prefix in ALLOWED_PREFIXES)
    if not allowed:
        return json.dumps({
            "error": (
                f"Access denied: only files under {ALLOWED_PREFIXES} can be written. "
                f"Got: '{file_path}'"
            ),
        })

    full_path = WORKSPACE / file_path

    # Guard against path traversal
    try:
        full_path.resolve().relative_to(WORKSPACE.resolve())
    except ValueError:
        return json.dumps({"error": "Path traversal detected — access denied."})

    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

    return json.dumps({
        "status": "written",
        "file_path": file_path,
        "bytes_written": len(content),
    })
