"""Tool to create a Linear issue for a dbt pipeline failure."""

import json
from typing import Optional

from strands import tool

from agent.linear_client import (
    ESTIMATE_MAP,
    PRIORITY_MAP,
    LinearClientError,
    get_linear_client,
)


def _build_description(
    summary: str,
    failed_models: list[str],
    error_messages: list[str],
    sql_snippets: list[str],
    run_id: str,
    command: str,
    exit_code: int,
    started_at: str | None,
) -> str:
    """Build markdown-formatted issue description."""
    models_block = "\n".join(f"- `{m}`" for m in failed_models) if failed_models else "- _(none identified)_"

    errors_block = "\n".join(
        f"```\n{e}\n```" for e in error_messages
    ) if error_messages else "_(no error messages captured)_"

    sql_block = "\n".join(
        f"```sql\n{s}\n```" for s in sql_snippets
    ) if sql_snippets else "_(no SQL captured)_"

    return f"""\
## Summary
{summary}

## Failed Models
{models_block}

## Error Details
{errors_block}

## SQL Source
{sql_block}

## Run Metadata
| Field | Value |
|-------|-------|
| Run ID | `{run_id}` |
| Command | `{command}` |
| Exit Code | `{exit_code}` |
| Started At | `{started_at or "unknown"}` |"""


@tool
def create_linear_issue(
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
    estimate_size: Optional[str] = None,
) -> str:
    """Create a Linear issue for a dbt pipeline failure.

    Creates an issue in the "Data Alerts" project in Linear with a
    structured markdown description containing all failure details.

    Args:
        run_id: The dbt run identifier (included in the description for traceability).
        title: A short descriptive title for the failure.
        severity: One of CRITICAL, HIGH, MEDIUM, LOW.  Mapped to Linear priority.
        summary: An LLM-generated summary explaining what went wrong and potential fixes.
        failed_models: List of dbt model names that failed.
        error_messages: List of error messages extracted from the dbt logs.
        sql_snippets: List of SQL source snippets from the failing models.
        command: The dbt command that was run (e.g. 'dbt run').
        exit_code: The process exit code.
        started_at: ISO-8601 timestamp of when the run started (optional).
        estimate_size: T-shirt size estimate for the fix effort: XS, S, M, L, or XL (optional).

    Returns:
        A JSON string with issue details (id, identifier, url) on success,
        or an error message on failure.
    """
    try:
        client = get_linear_client()

        description = _build_description(
            summary=summary,
            failed_models=failed_models,
            error_messages=error_messages,
            sql_snippets=sql_snippets,
            run_id=run_id,
            command=command,
            exit_code=exit_code,
            started_at=started_at,
        )

        priority = PRIORITY_MAP.get(severity.upper())
        estimate = ESTIMATE_MAP.get(estimate_size.upper()) if estimate_size else None

        issue = client.create_issue(
            title=title,
            description=description,
            priority=priority,
            estimate=estimate,
        )

        return json.dumps({
            "status": "created",
            "issue_id": issue.get("id", ""),
            "identifier": issue.get("identifier", ""),
            "url": issue.get("url", ""),
        })

    except LinearClientError as exc:
        return json.dumps({
            "status": "error",
            "error": str(exc),
        })
