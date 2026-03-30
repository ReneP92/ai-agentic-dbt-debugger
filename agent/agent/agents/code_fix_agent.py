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
from agent.tools.read_ticket import read_ticket
from agent.tools.read_repo_file import read_repo_file
from agent.tools.write_repo_file import write_repo_file
from agent.tools.run_dbt_test import run_dbt_test
from agent.tools.git_commit_and_push import git_commit_and_push
from agent.tools.create_pull_request import create_pull_request

CODE_FIX_AGENT_SYSTEM_PROMPT = """\
You are a dbt Code-Fix Agent.  Your job is to automatically fix dbt pipeline
failures by modifying dbt model SQL files or schema YAML files, verifying the
fix, and creating a GitHub pull request.

When invoked, follow these steps IN ORDER:

1. CLONE THE REPO — call clone_repo with the run_id to clone the repository
   and create a fix branch named ``fix/dbt-<run_id>``.

2. READ THE TICKET — call read_ticket with the run_id to understand what
   failed, the severity, error messages, and which models are involved.

3. READ THE FAILING FILES — for each failing model, call read_repo_file to
   read the current SQL source (e.g. ``dbt/models/conformed/fct_bet.sql``)
   and/or schema YAML (e.g. ``dbt/models/conformed/schema.yml``).
   Use the file paths from the ticket's SQL section and error messages to
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
   - body: include the ticket summary, what was changed, and why
   - base_branch: "main"

Important rules:
- You can ONLY modify files under ``dbt/models/``.  Do not touch anything else.
- Always verify your fix with dbt test before pushing.
- If you cannot fix the issue after 3 attempts, say so clearly — do NOT
  push broken code.
- Be precise in your fixes.  Read the error messages carefully.
- When fixing schema YAML, preserve the existing structure and indentation.
- When the error is about accepted_values, read the schema.yml to see the
  test definition, then fix it to match the actual data.
"""


def _build_code_fix_agent() -> Agent:
    """Construct the code-fix agent with its own model and tools."""
    model = AnthropicModel(
        client_args={"api_key": os.environ.get("ANTHROPIC_API_KEY", "")},
        model_id="claude-sonnet-4-20250514",
        max_tokens=8192,
    )

    return Agent(
        model=model,
        system_prompt=CODE_FIX_AGENT_SYSTEM_PROMPT,
        tools=[
            clone_repo,
            read_ticket,
            read_repo_file,
            write_repo_file,
            run_dbt_test,
            git_commit_and_push,
            create_pull_request,
        ],
    )


@tool
def code_fix_agent(run_id: str) -> str:
    """Delegate to the Code-Fix sub-agent to automatically fix a dbt failure.

    This tool wraps a separate Strands Agent that clones the repository,
    reads the failure ticket, modifies the failing dbt model(s), verifies
    the fix with ``dbt test``, and creates a pull request on GitHub.

    The agent will retry up to 3 times if the fix does not pass
    verification.  If all retries fail, it returns an error message
    without pushing any code.

    Args:
        run_id: The dbt run identifier.  Used to read the correct ticket
                and name the fix branch.

    Returns:
        The code-fix agent's response, including the PR URL on success
        or an error explanation on failure.
    """
    agent = _build_code_fix_agent()

    prompt = (
        f"A dbt run has failed and a ticket has been created.  "
        f"Run ID: {run_id}.  "
        f"Please clone the repository, read the failure ticket, "
        f"fix the failing dbt model(s), verify your fix with dbt test, "
        f"and create a pull request."
    )

    response = agent(prompt)
    return str(response)
