"""Live monitoring for dbt debugger agents.

Provides a ``MonitorHookProvider`` (Strands lifecycle hooks) and a
``MonitorCallbackHandler`` (streaming token capture) that push JSON
events over WebSocket to the monitor server.

Usage::

    from agent.monitor import setup_monitor

    monitor = setup_monitor(run_id="20240101_120000", agent_type="ticket")
    agent = Agent(
        model=model,
        hooks=[monitor.hook_provider],
        callback_handler=monitor.callback_handler,
    )
    response = agent("...")
    monitor.close()

If the ``MONITOR_WS_URL`` env var is not set, all operations are
graceful no-ops so the agents work without the monitor container.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any

# ── Strands hook imports ──────────────────────────────────────────────
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import (
    AfterInvocationEvent,
    AfterModelCallEvent,
    AfterToolCallEvent,
    BeforeInvocationEvent,
    BeforeModelCallEvent,
    BeforeToolCallEvent,
)

# WebSocket client (sync) — agent code is synchronous
try:
    import websocket as ws_client  # websocket-client package
except ImportError:
    ws_client = None  # type: ignore[assignment]


# ── Constants ─────────────────────────────────────────────────────────
_SUB_AGENT_TOOLS = {"ticket_agent", "code_fix_agent"}
_MAX_PAYLOAD = 2000  # Truncate tool input/result payloads to this length

# Claude Sonnet 4 pricing (USD per 1M tokens)
PRICING = {
    "input": 3.00,
    "output": 15.00,
    "cache_read": 0.30,
    "cache_write": 3.75,
}


def _truncate(value: Any, max_len: int = _MAX_PAYLOAD) -> str:
    """Convert value to string and truncate if needed."""
    s = str(value) if not isinstance(value, str) else value
    if len(s) > max_len:
        return s[:max_len] + f"... ({len(s) - max_len} chars truncated)"
    return s


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── MonitorHookProvider ───────────────────────────────────────────────
class MonitorHookProvider(HookProvider):
    """Captures Strands lifecycle events and pushes them over WebSocket."""

    def __init__(self, ws_url: str, run_id: str, agent_type: str) -> None:
        self.ws_url = ws_url
        self.run_id = run_id
        self.agent_type = agent_type
        self._ws: Any = None
        self._lock = threading.Lock()
        self._connected = False
        # Track tool call start times for duration calculation
        self._tool_start_times: dict[str, float] = {}

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self._on_invocation_start)
        registry.add_callback(AfterInvocationEvent, self._on_invocation_end)
        registry.add_callback(BeforeModelCallEvent, self._on_model_start)
        registry.add_callback(AfterModelCallEvent, self._on_model_end)
        registry.add_callback(BeforeToolCallEvent, self._on_tool_start)
        registry.add_callback(AfterToolCallEvent, self._on_tool_end)

    # ── Hook handlers ─────────────────────────────────────────────────

    def _on_invocation_start(self, event: BeforeInvocationEvent) -> None:
        self.emit("invocation_start", agent_name=self.agent_type)

    def _on_invocation_end(self, event: AfterInvocationEvent) -> None:
        data: dict[str, Any] = {
            "agent_name": self.agent_type,
            "stop_reason": event.result.stop_reason if event.result else None,
        }
        # Attach accumulated metrics from the result
        if event.result and hasattr(event.result, "metrics"):
            metrics = event.result.metrics
            usage = getattr(metrics, "accumulated_usage", {})
            data["metrics"] = {
                "input_tokens": usage.get("inputTokens", 0),
                "output_tokens": usage.get("outputTokens", 0),
                "total_tokens": usage.get("totalTokens", 0),
                "cache_read_tokens": usage.get("cacheReadInputTokens", 0),
                "cache_write_tokens": usage.get("cacheWriteInputTokens", 0),
                "latency_ms": getattr(metrics, "accumulated_metrics", {}).get("latencyMs", 0),
                "cycle_count": getattr(metrics, "cycle_count", 0),
            }
            # Compute estimated cost
            u = data["metrics"]
            cost = (
                u["input_tokens"] * PRICING["input"]
                + u["output_tokens"] * PRICING["output"]
                + u["cache_read_tokens"] * PRICING["cache_read"]
                + u["cache_write_tokens"] * PRICING["cache_write"]
            ) / 1_000_000
            data["metrics"]["estimated_cost_usd"] = round(cost, 6)

            # Per-tool metrics
            tool_metrics = getattr(metrics, "tool_metrics", {})
            if tool_metrics:
                data["metrics"]["tools"] = {
                    name: {
                        "call_count": tm.call_count,
                        "success_count": tm.success_count,
                        "error_count": tm.error_count,
                        "total_time_s": round(tm.total_time, 2),
                    }
                    for name, tm in tool_metrics.items()
                }

        self.emit("invocation_end", **data)

    def _on_model_start(self, event: BeforeModelCallEvent) -> None:
        self.emit("model_call_start", agent_name=self.agent_type)

    def _on_model_end(self, event: AfterModelCallEvent) -> None:
        data: dict[str, Any] = {"agent_name": self.agent_type}
        if event.stop_response:
            data["stop_reason"] = event.stop_response.stop_reason
        if event.exception:
            data["error"] = str(event.exception)
        self.emit("model_call_end", **data)

    def _on_tool_start(self, event: BeforeToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "unknown")
        tool_use_id = event.tool_use.get("toolUseId", "")

        # Record start time for duration calculation
        self._tool_start_times[tool_use_id] = time.time()

        # Detect sub-agent delegation
        if tool_name in _SUB_AGENT_TOOLS:
            self.emit("sub_agent_start", sub_agent_name=tool_name,
                      tool_use_id=tool_use_id,
                      input=_truncate(event.tool_use.get("input", {})))
        else:
            self.emit("tool_start", tool_name=tool_name,
                      tool_use_id=tool_use_id,
                      input=_truncate(event.tool_use.get("input", {})))

    def _on_tool_end(self, event: AfterToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "unknown")
        tool_use_id = event.tool_use.get("toolUseId", "")

        # Calculate duration
        start_t = self._tool_start_times.pop(tool_use_id, None)
        duration_s = round(time.time() - start_t, 2) if start_t else None

        data: dict[str, Any] = {
            "tool_name": tool_name,
            "tool_use_id": tool_use_id,
        }
        if duration_s is not None:
            data["duration_s"] = duration_s

        if event.exception:
            data["status"] = "error"
            data["error"] = str(event.exception)
        else:
            data["status"] = event.result.get("status", "success") if isinstance(event.result, dict) else "success"
            data["result"] = _truncate(event.result)

        # Detect sub-agent delegation
        if tool_name in _SUB_AGENT_TOOLS:
            self.emit("sub_agent_end", **data)
        else:
            self.emit("tool_end", **data)

    # ── WebSocket transport ───────────────────────────────────────────

    def _connect(self) -> bool:
        """Lazily connect to the monitor WebSocket server."""
        if self._connected:
            return True
        if not ws_client:
            return False

        with self._lock:
            if self._connected:
                return True
            try:
                self._ws = ws_client.WebSocket()
                self._ws.settimeout(5)
                self._ws.connect(self.ws_url)
                self._connected = True
                print(f"[monitor] Connected to {self.ws_url}", file=sys.stderr)
                return True
            except Exception as exc:
                print(f"[monitor] Could not connect to {self.ws_url}: {exc}", file=sys.stderr)
                return False

    def emit(self, event_type: str, **data: Any) -> None:
        """Send an event to the monitor server. Fire-and-forget."""
        event = {
            "type": event_type,
            "run_id": self.run_id,
            "agent": self.agent_type,
            "timestamp": _now_iso(),
            "data": data,
        }

        if not self._connect():
            return

        try:
            self._ws.send(json.dumps(event))
        except Exception:
            # Connection lost — try to reconnect once
            self._connected = False
            if self._connect():
                try:
                    self._ws.send(json.dumps(event))
                except Exception:
                    pass  # silently drop

    def close(self) -> None:
        """Close the WebSocket connection."""
        if self._ws and self._connected:
            try:
                self._ws.close()
            except Exception:
                pass
            self._connected = False


# ── MonitorCallbackHandler ────────────────────────────────────────────
class MonitorCallbackHandler:
    """Captures streaming tokens and reasoning from the LLM.

    Buffers text chunks and flushes them periodically to avoid
    overwhelming the WebSocket with per-token messages.
    """

    def __init__(self, hook_provider: MonitorHookProvider) -> None:
        self._provider = hook_provider
        self._text_buffer: list[str] = []
        self._reasoning_buffer: list[str] = []
        self._last_flush = time.time()
        self._flush_interval = 0.15  # seconds

    def __call__(self, **kwargs: Any) -> None:
        # Streaming text token
        if "data" in kwargs:
            self._text_buffer.append(kwargs["data"])
            self._maybe_flush()

        # Reasoning/thinking token
        if "reasoningText" in kwargs:
            self._reasoning_buffer.append(kwargs["reasoningText"])
            self._maybe_flush()

        # Final result
        if "result" in kwargs:
            self._flush()

    def _maybe_flush(self) -> None:
        now = time.time()
        if now - self._last_flush >= self._flush_interval:
            self._flush()

    def _flush(self) -> None:
        if self._text_buffer:
            text = "".join(self._text_buffer)
            self._text_buffer.clear()
            self._provider.emit("token", text=text)

        if self._reasoning_buffer:
            text = "".join(self._reasoning_buffer)
            self._reasoning_buffer.clear()
            self._provider.emit("reasoning", text=text)

        self._last_flush = time.time()


# ── Monitor facade ────────────────────────────────────────────────────
class Monitor:
    """Convenience wrapper that bundles the hook provider and callback handler."""

    def __init__(self, hook_provider: MonitorHookProvider, callback_handler: MonitorCallbackHandler) -> None:
        self.hook_provider = hook_provider
        self.callback_handler = callback_handler

    def emit(self, event_type: str, **data: Any) -> None:
        self.hook_provider.emit(event_type, **data)

    def close(self) -> None:
        self.hook_provider.close()


class _NullMonitor:
    """No-op monitor when MONITOR_WS_URL is not set."""

    hook_provider = None
    callback_handler = None

    def emit(self, event_type: str, **data: Any) -> None:
        pass

    def close(self) -> None:
        pass


def setup_monitor(run_id: str, agent_type: str) -> Monitor | _NullMonitor:
    """Create a Monitor connected to the WebSocket server.

    Returns a ``_NullMonitor`` if ``MONITOR_WS_URL`` is not set or
    ``websocket-client`` is not installed.
    """
    ws_url = os.environ.get("MONITOR_WS_URL")
    if not ws_url or not ws_client:
        if not ws_url:
            print("[monitor] MONITOR_WS_URL not set, monitoring disabled", file=sys.stderr)
        return _NullMonitor()

    provider = MonitorHookProvider(ws_url=ws_url, run_id=run_id, agent_type=agent_type)
    handler = MonitorCallbackHandler(provider)
    return Monitor(hook_provider=provider, callback_handler=handler)
