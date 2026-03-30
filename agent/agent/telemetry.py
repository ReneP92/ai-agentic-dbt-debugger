"""OpenTelemetry setup for exporting Strands agent traces to Langfuse.

Call ``setup_telemetry()`` once at process startup, before any Agent is
created.  It reads the Langfuse credentials and OTLP endpoint from the
environment (set via docker-compose) and configures the Strands
``StrandsTelemetry`` OTLP exporter.

If the required env vars are not set, telemetry is silently skipped so
the agents still work without Langfuse.
"""

import base64
import os


def setup_telemetry() -> None:
    """Configure OTLP trace export to Langfuse if credentials are available."""
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

    if not all([public_key, secret_key, endpoint]):
        print("[telemetry] Langfuse credentials not set, skipping OTEL export")
        return

    # Langfuse expects Basic Auth: base64(public_key:secret_key)
    auth_string = base64.b64encode(
        f"{public_key}:{secret_key}".encode()
    ).decode()

    # Set OTEL env vars so StrandsTelemetry picks them up
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {auth_string}"

    try:
        from strands.telemetry import StrandsTelemetry

        telemetry = StrandsTelemetry()
        telemetry.setup_otlp_exporter()
        print(f"[telemetry] OTEL export configured -> {endpoint}")
    except ImportError:
        print("[telemetry] strands-agents[otel] not installed, skipping OTEL export")
    except Exception as exc:
        # Don't crash the agent if telemetry setup fails
        print(f"[telemetry] Failed to configure OTEL export: {exc}")
