"""Entrypoint for the dbt code-fix agent.

Usage:
    python -m agent.code_fix_main <run_id>

Invokes the Code-Fix sub-agent which clones the repository, reads the
failure ticket, attempts to fix the failing dbt model(s), verifies the
fix with ``dbt test``, and creates a GitHub pull request.

Exits with code 0 on success, 1 on failure.
"""

import os
import sys

from strands import Agent
from strands.models.anthropic import AnthropicModel

from agent.agents.code_fix_agent import code_fix_agent


def build_code_fix_orchestrator() -> Agent:
    """Construct a lightweight orchestrator that delegates to the code-fix agent."""
    model = AnthropicModel(
        client_args={"api_key": os.environ.get("ANTHROPIC_API_KEY", "")},
        model_id="claude-sonnet-4-20250514",
        max_tokens=4096,
    )

    return Agent(
        model=model,
        system_prompt=(
            "You are a Code-Fix Orchestrator.  When given a dbt run ID, "
            "delegate to the code_fix_agent tool to attempt an automated fix.  "
            "Report the result: either the PR URL on success, or a clear "
            "explanation of why the fix could not be applied."
        ),
        tools=[code_fix_agent],
    )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m agent.code_fix_main <run_id>", file=sys.stderr)
        sys.exit(1)

    run_id = sys.argv[1]

    print(f"[code-fix] Attempting automated fix for failed dbt run: {run_id}")

    orchestrator = build_code_fix_orchestrator()
    response = orchestrator(
        f"A dbt run has failed and a ticket exists.  Run ID: {run_id}.  "
        f"Please invoke the code-fix agent to attempt an automated fix."
    )

    response_str = str(response)
    print(f"\n[code-fix] Done. Response:\n{response_str}")

    # Exit with error if the fix was not successfully applied
    # Look for signs of failure in the response
    failure_indicators = [
        "could not",
        "failed to",
        "unable to",
        "all retries",
        "retry exhausted",
        "did not pass",
        "fix was not applied",
    ]
    response_lower = response_str.lower()
    if any(indicator in response_lower for indicator in failure_indicators):
        sys.exit(1)


if __name__ == "__main__":
    main()
