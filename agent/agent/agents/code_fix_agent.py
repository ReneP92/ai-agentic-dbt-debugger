"""Code-Fix sub-agent.

A dedicated Strands Agent that attempts to automatically fix dbt failures
by reading the failure ticket, modifying dbt model SQL or schema YAML,
verifying the fix with ``dbt test``, and creating a GitHub pull request.

Exposed as a @tool so the code-fix orchestrator can invoke it via the
"agents as tools" pattern.
"""

import os

from strands import Agent, tool
from strands.models.anthropic import AnthropicModel

from agent.tools.clone_repo import clone_repo
from agent.tools.read_linear_issue import read_linear_issue
from agent.tools.comment_linear_issue import comment_linear_issue
from agent.tools.read_repo_file import read_repo_file
from agent.tools.write_repo_file import write_repo_file
from agent.tools.run_dbt_test import run_dbt_test
from agent.tools.git_commit_and_push import git_commit_and_push
from agent.tools.create_pull_request import create_pull_request
from agent.tools.query_snowflake import query_snowflake

CODE_FIX_AGENT_SYSTEM_PROMPT = """\
You are a dbt Code-Fix Agent.  Your job is to automatically fix dbt pipeline
failures by modifying dbt model SQL files or schema YAML files, verifying the
fix, and creating a GitHub pull request.

When invoked, follow these steps IN ORDER:

1. CLONE THE REPO — call clone_repo with the run_id to clone the repository
   and create a fix branch named ``fix/dbt-<run_id>``.

2. READ THE LINEAR ISSUE — call read_linear_issue with the run_id to
   understand what failed, the severity, error messages, and which models
   are involved.

3. READ THE FAILING FILES — for each failing model, call read_repo_file to
   read the current SQL source (e.g. ``dbt/models/conformed/fct_bet.sql``)
   and/or schema YAML (e.g. ``dbt/models/conformed/schema.yml``).
   Use the file paths from the issue's SQL section and error messages to
   determine which files to read.

4. WRITE THE FIX — call write_repo_file to write the corrected file content.
   Only modify files under ``dbt/models/``.  Common fixes include:
   - Fixing SQL syntax errors (typos, missing commas, wrong column names)
   - Correcting schema test configurations (e.g. accepted_values lists)
   - Fixing JOIN conditions or WHERE clauses
   - Adding missing columns or correcting column references

5. VERIFY THE FIX — call run_dbt_test with the model name to run
   ``dbt test --select <model>`` against LocalStack Snowflake.
   - If the test PASSES → proceed to step 6.
   - If the test FAILS → read the error output, adjust your fix, and retry.
     You may retry up to 3 times total.  If all retries fail, respond with
     a clear error message explaining what you tried and why it failed.
     Do NOT commit or push if the fix does not pass verification.

6. COMMIT AND PUSH — call git_commit_and_push with a descriptive commit
   message and the branch name.

7. CREATE PULL REQUEST — call create_pull_request with:
   - branch_name: the fix branch
   - title: a concise description of the fix
   - body: include the issue summary, what was changed, and why
   - base_branch: "main"

8. LINK PR TO LINEAR ISSUE — call comment_linear_issue with the Linear
   issue UUID (from step 2) and a comment body that includes the PR URL,
   a brief summary of the fix, and what files were changed.

Important rules:
- You can ONLY modify files under ``dbt/models/``.  Do not touch anything else.
- Always verify your fix with dbt test before pushing.
- If you cannot fix the issue after 3 attempts, say so clearly — do NOT
  push broken code.
- Be precise in your fixes.  Read the error messages carefully.
- When fixing schema YAML, preserve the existing structure and indentation.
- When the error is about accepted_values, read the schema.yml to see the
  test definition, then fix it to match the actual data.

You also have access to query_snowflake to run read-only SELECT queries
against the LocalStack Snowflake database (database: BETTING).  Use this
to inspect actual data when debugging — for example:
- Check distinct values in a column when an accepted_values test fails:
  ``SELECT DISTINCT column_name FROM BETTING.schema.table``
- Verify row counts or data distributions after applying a fix.
- Examine source data to understand the root cause of a failure.
Only SELECT queries are allowed.  Results are capped at 100 rows.
"""

# Module-level monitor reference — set by the entrypoint before agent runs
_monitor = None


def set_monitor(monitor) -> None:
    """Set the shared monitor instance for sub-agent observability."""
    global _monitor
    _monitor = monitor


def _build_code_fix_agent() -> Agent:
    """Construct the code-fix agent with its own model and tools."""
    model = AnthropicModel(
        client_args={"api_key": os.environ.get("ANTHROPIC_API_KEY", "")},
        model_id="claude-sonnet-4-20250514",
        max_tokens=8192,
    )

    kwargs = {}
    if _monitor and _monitor.hook_provider:
        kwargs["hooks"] = [_monitor.hook_provider]
        kwargs["callback_handler"] = _monitor.callback_handler

    return Agent(
        model=model,
        system_prompt=CODE_FIX_AGENT_SYSTEM_PROMPT,
        tools=[
            clone_repo,
            read_linear_issue,
            comment_linear_issue,
            read_repo_file,
            write_repo_file,
            run_dbt_test,
            git_commit_and_push,
            create_pull_request,
            query_snowflake,
        ],
        **kwargs,
    )


@tool
def code_fix_agent(run_id: str) -> str:
    """Delegate to the Code-Fix sub-agent to automatically fix a dbt failure.

    This tool wraps a separate Strands Agent that clones the repository,
    reads the failure issue from Linear, modifies the failing dbt model(s),
    verifies the fix with ``dbt test``, creates a pull request on GitHub,
    and comments on the Linear issue with the PR link.

    The agent will retry up to 3 times if the fix does not pass
    verification.  If all retries fail, it returns an error message
    without pushing any code.

    Args:
        run_id: The dbt run identifier.  Used to find the Linear issue
                and name the fix branch.

    Returns:
        The code-fix agent's response, including the PR URL on success
        or an error explanation on failure.
    """
    agent = _build_code_fix_agent()

    prompt = (
        f"A dbt run has failed and a Linear issue has been created.  "
        f"Run ID: {run_id}.  "
        f"Please clone the repository, read the failure issue from Linear, "
        f"fix the failing dbt model(s), verify your fix with dbt test, "
        f"create a pull request, and comment on the Linear issue with the PR link."
    )

    response = agent(prompt)
    return str(response)
