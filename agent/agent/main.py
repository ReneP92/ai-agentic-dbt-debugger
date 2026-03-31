"""Entrypoint for the dbt debugger agent.

Usage:
    python -m agent.main <run_id>

    Or via the installed script:
    dbt-debugger <run_id>
"""

import sys
import time
import warnings

from agent.monitor import setup_monitor
from agent.orchestrator import build_orchestrator
from agent.agents.ticket_agent import set_monitor as set_ticket_monitor

# Suppress Pydantic serialization warnings from the Anthropic SDK
# (ParsedTextBlock vs expected block type mismatches).
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m agent.main <run_id>", file=sys.stderr)
        sys.exit(1)

    run_id = sys.argv[1]

    # Set up live monitoring (no-op if MONITOR_WS_URL not set)
    monitor = setup_monitor(run_id=run_id, agent_type="ticket")
    set_ticket_monitor(monitor)

    print(f"[agent] Investigating failed dbt run: {run_id}")
    monitor.emit("run_start", agent_type="ticket")

    start = time.time()
    orchestrator = build_orchestrator(
        run_id=run_id,
        monitor=monitor,
    )

    try:
        response = orchestrator(
            f"A dbt run has failed.  Run ID: {run_id}.  "
            f"Please investigate the failure and create a Linear issue."
        )
    except Exception as exc:
        duration = time.time() - start
        print(f"\n[agent] FATAL: Agent crashed: {exc}", file=sys.stderr)
        monitor.emit("run_end", agent_type="ticket", success=False, duration_s=round(duration, 2))
        monitor.close()
        sys.exit(1)

    response_str = str(response)
    duration = time.time() - start

    # Detect whether the Linear issue was actually created
    failure_indicators = [
        "could not",
        "failed to",
        "unable to",
        "error",
        "api connection issue",
        "not configured",
    ]
    response_lower = response_str.lower()
    success = not any(indicator in response_lower for indicator in failure_indicators)

    monitor.emit("run_end", agent_type="ticket", success=success, duration_s=round(duration, 2))
    monitor.close()

    print(f"\n[agent] Done. Response:\n{response_str}")

    if not success:
        print("[agent] FATAL: Ticket creation failed — aborting pipeline.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
