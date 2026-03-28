"""Tool to read the SQL source of a dbt model by name."""

import json
from pathlib import Path

from strands import tool

MODELS_BASE = Path("/usr/app/dbt/models")


@tool
def read_model_sql(model_name: str) -> str:
    """Read the SQL source code of a dbt model by its name.

    Searches the dbt models directory for a .sql file matching the given
    model name (without extension).  This is used to retrieve the SQL that
    caused a failure so it can be included in the ticket.

    Args:
        model_name: The dbt model name (e.g. 'fct_bet', 'std_user').
                    Do not include the .sql extension or directory path.

    Returns:
        A JSON string with 'model_name', 'file_path', and 'sql' fields,
        or an error message if the model is not found.
    """
    # Search recursively for the matching .sql file
    matches = list(MODELS_BASE.rglob(f"{model_name}.sql"))

    if not matches:
        return json.dumps(
            {"error": f"No SQL file found for model '{model_name}' under {MODELS_BASE}"}
        )

    # Use the first match (model names should be unique in dbt)
    sql_path = matches[0]

    return json.dumps(
        {
            "model_name": model_name,
            "file_path": str(sql_path),
            "sql": sql_path.read_text(),
        },
        indent=2,
    )
