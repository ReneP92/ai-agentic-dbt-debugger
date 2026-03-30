"""Entrypoint for the dbt debugger agent.

Usage:
    python -m agent.main <run_id>

    Or via the installed script:
    dbt-debugger <run_id>
"""

import sys
import warnings

from agent.orchestrator import build_orchestrator

# Suppress Pydantic serialization warnings from the Anthropic SDK
# (ParsedTextBlock vs expected block type mismatches).
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m agent.main <run_id>", file=sys.stderr)
        sys.exit(1)

    run_id = sys.argv[1]

    print(f"[agent] Investigating failed dbt run: {run_id}")

    orchestrator = build_orchestrator()
    response = orchestrator(
        f"A dbt run has failed.  Run ID: {run_id}.  "
        f"Please investigate the failure and create a ticket."
    )

    print(f"\n[agent] Done. Response:\n{response}")


if __name__ == "__main__":
    main()
