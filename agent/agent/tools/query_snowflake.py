"""Tool to run read-only SQL queries against LocalStack Snowflake."""

import json
import re

from strands import tool

# Connection parameters matching dbt/profiles.yml (LocalStack Snowflake).
SNOWFLAKE_CONFIG = {
    "account": "localstack",
    "host": "snowflake.localhost.localstack.cloud",
    "port": 4566,
    "user": "test",
    "password": "test",
    "database": "BETTING",
    "warehouse": "TRANSFORM",
    "role": "test",
    "protocol": "http",
}

# Maximum rows to return (prevents dumping huge result sets into context).
MAX_ROWS = 100


def _is_select_only(query: str) -> bool:
    """Check that the query is a SELECT statement (no mutations)."""
    # Strip leading whitespace and SQL comments
    cleaned = re.sub(r"--.*$", "", query, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip().upper()

    # Must start with SELECT, WITH (CTE), or SHOW/DESCRIBE (read-only metadata)
    allowed_prefixes = ("SELECT", "WITH", "SHOW", "DESCRIBE", "DESC")
    return any(cleaned.startswith(prefix) for prefix in allowed_prefixes)


def _has_limit(query: str) -> bool:
    """Check if the query already contains a LIMIT clause."""
    cleaned = re.sub(r"--.*$", "", query, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    return bool(re.search(r"\bLIMIT\b", cleaned, re.IGNORECASE))


@tool
def query_snowflake(query: str) -> str:
    """Run a read-only SQL query against the LocalStack Snowflake database.

    Use this tool to inspect actual data when debugging dbt failures — for
    example, to check distinct values in a column when an ``accepted_values``
    test fails, to examine row counts, or to verify data after applying a fix.

    Only ``SELECT``, ``WITH`` (CTE), ``SHOW``, and ``DESCRIBE`` statements
    are allowed.  Mutations (INSERT, UPDATE, DELETE, DROP, etc.) will be
    rejected.  Results are capped at 100 rows.

    Args:
        query: The SQL query to execute.  Must be a read-only statement.

    Returns:
        A JSON string with ``columns`` (list of column names), ``rows``
        (list of row dicts), and ``row_count``.  Returns an error message
        if the query is not allowed or execution fails.
    """
    if not _is_select_only(query):
        return json.dumps({
            "error": (
                "Only SELECT, WITH, SHOW, and DESCRIBE queries are allowed. "
                "Mutations are not permitted."
            ),
        })

    # Append LIMIT if not present to prevent huge result sets
    if not _has_limit(query):
        query = f"{query.rstrip().rstrip(';')} LIMIT {MAX_ROWS}"

    try:
        import snowflake.connector

        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        try:
            cursor = conn.cursor()
            cursor.execute(query)

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchmany(MAX_ROWS)

            # Convert rows to list of dicts for readability
            row_dicts = [dict(zip(columns, row)) for row in rows]

            # Convert any non-serializable values to strings
            for row_dict in row_dicts:
                for key, value in row_dict.items():
                    if not isinstance(value, (str, int, float, bool, type(None))):
                        row_dict[key] = str(value)

            return json.dumps({
                "columns": columns,
                "rows": row_dicts,
                "row_count": len(row_dicts),
            }, indent=2, default=str)

        finally:
            conn.close()

    except Exception as e:
        return json.dumps({
            "error": f"Query execution failed: {type(e).__name__}: {e}",
        })
