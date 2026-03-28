"""Orchestrator Agent.

The top-level agent that reacts to dbt run failures.  It reads the run
manifest and logs, retrieves the SQL of any failing models, and delegates
to the Ticket Creator sub-agent to produce a structured failure ticket.
"""

import os

from strands import Agent
from strands.models.anthropic import AnthropicModel

from agent.agents.ticket_agent import ticket_agent
from agent.tools.read_dbt_logs import read_dbt_logs
from agent.tools.read_dbt_manifest import read_dbt_manifest
from agent.tools.read_model_sql import read_model_sql

ORCHESTRATOR_SYSTEM_PROMPT = """\
You are a dbt Pipeline Debugger — an orchestrator agent responsible for
investigating dbt run failures and ensuring a ticket is created.

When invoked with a run ID, follow these steps IN ORDER:

1. READ THE MANIFEST — call read_dbt_manifest with the run_id to get the
   run metadata (command, exit code, timestamp, success flag).

2. READ THE LOGS — call read_dbt_logs with the run_id to extract error
   and warning entries.  Identify which model(s) failed from the node_id
   fields.

3. READ THE SQL — for each failed model identified in step 2, call
   read_model_sql with the model name (e.g. if node_id is
   "model.betting_platform.fct_bet", the model name is "fct_bet").

4. DELEGATE TO TICKET AGENT — call ticket_agent with all the gathered
   context: run_id, command, exit_code, started_at, failed_models,
   error_messages, and sql_snippets.  The ticket agent will classify
   severity, write a summary, and persist the ticket file.

5. REPORT — once the ticket agent confirms the ticket was created,
   output a brief confirmation message with the ticket path and severity.

Important:
- Always complete all steps.  Do not skip reading the SQL.
- Extract model names from node IDs by taking the last segment after the
  final dot (e.g. "model.betting_platform.fct_bet" → "fct_bet").
- If the logs contain no identifiable failed models, still create a ticket
  with the available error messages.
"""


def build_orchestrator() -> Agent:
    """Construct the orchestrator agent with all tools wired up."""
    model = AnthropicModel(
        client_args={"api_key": os.environ.get("ANTHROPIC_API_KEY", "")},
        model_id="claude-sonnet-4-20250514",
        max_tokens=4096,
    )

    return Agent(
        model=model,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=[
            read_dbt_manifest,
            read_dbt_logs,
            read_model_sql,
            ticket_agent,
        ],
    )
