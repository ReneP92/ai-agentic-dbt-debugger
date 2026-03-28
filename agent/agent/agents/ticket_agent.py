"""Ticket Creator sub-agent.

A dedicated Strands Agent with its own system prompt, responsible for
analyzing dbt failure context and writing a well-structured ticket.
Exposed as a @tool so the orchestrator can invoke it via the
"agents as tools" pattern.
"""

import os

from strands import Agent, tool
from strands.models.anthropic import AnthropicModel

from agent.tools.create_ticket import create_ticket

TICKET_AGENT_SYSTEM_PROMPT = """\
You are a Ticket Creator agent specialising in dbt pipeline failures.

Your job:
1. Receive structured information about a failed dbt run (error messages,
   failed model names, SQL source code, and run metadata).
2. Write a concise but informative SUMMARY that explains:
   - What failed and why (root cause if identifiable).
   - The likely impact on downstream models/dashboards.
   - Suggested next steps or fixes.
3. Classify the SEVERITY as one of:
   - CRITICAL: Production data pipeline is broken; downstream consumers
     are receiving stale or incorrect data.
   - HIGH: A key model failed but the pipeline partially succeeded;
     some consumers may be affected.
   - MEDIUM: A non-critical model or test failed; impact is limited.
   - LOW: A warning or cosmetic issue; no data quality impact.
4. Call the create_ticket tool with all the information to persist the ticket.

Be direct, technical, and actionable.  Do NOT include pleasantries or filler.
"""


def _build_ticket_agent() -> Agent:
    """Construct the ticket creator agent with its own model and tools."""
    model = AnthropicModel(
        client_args={"api_key": os.environ.get("ANTHROPIC_API_KEY", "")},
        model_id="claude-sonnet-4-20250514",
        max_tokens=4096,
    )

    return Agent(
        model=model,
        system_prompt=TICKET_AGENT_SYSTEM_PROMPT,
        tools=[create_ticket],
    )


@tool
def ticket_agent(
    run_id: str,
    command: str,
    exit_code: int,
    started_at: str,
    failed_models: list[str],
    error_messages: list[str],
    sql_snippets: list[str],
) -> str:
    """Delegate to the Ticket Creator sub-agent to analyse a dbt failure and persist a ticket.

    This tool wraps a separate Strands Agent that has its own system prompt
    focused on failure analysis, severity classification, and ticket writing.
    The orchestrator should call this tool after it has gathered all the
    failure context from the dbt logs and model SQL.

    Args:
        run_id: The dbt run identifier.
        command: The dbt command that was executed (e.g. 'dbt run').
        exit_code: The process exit code of the dbt run.
        started_at: ISO-8601 timestamp of when the run started.
        failed_models: List of dbt model names that failed.
        error_messages: List of error messages extracted from the logs.
        sql_snippets: List of SQL source code from the failing models.

    Returns:
        The ticket agent's response including confirmation of the ticket file created.
    """
    agent = _build_ticket_agent()

    prompt = (
        f"A dbt run has failed.  Here is the context:\n\n"
        f"Run ID: {run_id}\n"
        f"Command: {command}\n"
        f"Exit Code: {exit_code}\n"
        f"Started At: {started_at}\n\n"
        f"Failed Models: {', '.join(failed_models) if failed_models else 'unknown'}\n\n"
        f"Error Messages:\n"
        + "\n---\n".join(error_messages)
        + "\n\n"
        f"SQL Source Code:\n"
        + "\n---\n".join(sql_snippets)
        + "\n\n"
        f"Please analyse the failure, classify its severity, write a summary, "
        f"and create the ticket."
    )

    response = agent(prompt)
    return str(response)
