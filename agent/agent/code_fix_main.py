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
import time
import warnings

from strands import Agent
from strands.models.anthropic import AnthropicModel

from agent.agents.code_fix_agent import code_fix_agent
from agent.agents.code_fix_agent import set_monitor as set_code_fix_monitor
from agent.monitor import setup_monitor
from agent.retry import invoke_with_retry

# Suppress Pydantic serialization warnings from the Anthropic SDK
# (ParsedTextBlock vs expected block type mismatches).
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")


def build_code_fix_orchestrator(run_id: str = "", monitor=None) -> Agent:
    """Construct a lightweight orchestrator that delegates to the code-fix agent."""
    model = AnthropicModel(
        client_args={"api_key": os.environ.get("ANTHROPIC_API_KEY", "")},
        model_id="claude-sonnet-4-6",
        max_tokens=4096,
    )

    kwargs = {}
    if monitor:
        kwargs["hooks"] = [monitor.hook_provider]
        kwargs["callback_handler"] = monitor.callback_handler

    return Agent(
        model=model,
        system_prompt=(
            "You are a Code-Fix Orchestrator.  When given a dbt run ID, "
            "delegate to the code_fix_agent tool to attempt an automated fix.  "
            "Report the result: either the PR URL on success, or a clear "
            "explanation of why the fix could not be applied."
        ),
        tools=[code_fix_agent],
        **kwargs,
    )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m agent.code_fix_main <run_id>", file=sys.stderr)
        sys.exit(1)

    run_id = sys.argv[1]

    # Set up live monitoring (no-op if MONITOR_WS_URL not set)
    monitor = setup_monitor(run_id=run_id, agent_type="code-fix")
    set_code_fix_monitor(monitor)

    print(f"[code-fix] Attempting automated fix for failed dbt run: {run_id}")
    monitor.emit("run_start", agent_type="code-fix")

    start = time.time()
    orchestrator = build_code_fix_orchestrator(run_id=run_id, monitor=monitor)

    try:
        response = invoke_with_retry(
            orchestrator,
            f"A dbt run has failed and a Linear issue has been created.  Run ID: {run_id}.  "
            f"Please invoke the code-fix agent to attempt an automated fix.",
            label="code-fix",
        )
    except Exception as exc:
        duration = time.time() - start
        print(f"\n[code-fix] FATAL: Agent crashed: {exc}", file=sys.stderr)
        monitor.emit("run_end", agent_type="code-fix", success=False, duration_s=round(duration, 2))
        monitor.close()
        sys.exit(1)

    response_str = str(response)
    duration = time.time() - start
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
    success = not any(indicator in response_lower for indicator in failure_indicators)

    monitor.emit("run_end", agent_type="code-fix", success=success, duration_s=round(duration, 2))
    monitor.close()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
