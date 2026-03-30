"""SQLite storage layer for the agent monitor."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any


DB_PATH = os.environ.get("MONITOR_DB_PATH", "/app/data/monitor.db")
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Get a thread-local SQLite connection."""
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA synchronous=NORMAL")
    return _local.conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = _get_conn()
    schema = SCHEMA_PATH.read_text()
    conn.executescript(schema)
    conn.commit()


def store_event(event: dict[str, Any]) -> None:
    """Store a single agent event."""
    conn = _get_conn()
    run_id = event.get("run_id", "")
    event_type = event.get("type", "")
    agent_name = event.get("agent", "")
    timestamp = event.get("timestamp", "")
    data = json.dumps(event.get("data", {}))

    # Upsert run record on run_start
    if event_type == "run_start":
        conn.execute(
            """INSERT INTO runs (run_id, agent_type, started_at)
               VALUES (?, ?, ?)
               ON CONFLICT(run_id) DO UPDATE SET
                 agent_type = excluded.agent_type,
                 started_at = excluded.started_at""",
            (run_id, event.get("data", {}).get("agent_type", agent_name), timestamp),
        )

    # Update run record on run_end
    if event_type == "run_end":
        run_data = event.get("data", {})
        conn.execute(
            """UPDATE runs SET
                 ended_at = ?,
                 success = ?,
                 total_duration_s = ?
               WHERE run_id = ?""",
            (
                timestamp,
                1 if run_data.get("success") else 0,
                run_data.get("duration_s"),
                run_id,
            ),
        )

    # Update token metrics on invocation_end
    if event_type == "invocation_end":
        metrics = event.get("data", {}).get("metrics", {})
        if metrics:
            conn.execute(
                """UPDATE runs SET
                     total_input_tokens = ?,
                     total_output_tokens = ?,
                     estimated_cost_usd = ?
                   WHERE run_id = ?""",
                (
                    metrics.get("input_tokens", 0),
                    metrics.get("output_tokens", 0),
                    metrics.get("estimated_cost_usd"),
                    run_id,
                ),
            )

    # Store the event
    conn.execute(
        """INSERT INTO events (run_id, type, agent_name, timestamp, data)
           VALUES (?, ?, ?, ?, ?)""",
        (run_id, event_type, agent_name, timestamp, data),
    )

    conn.commit()


def get_runs(limit: int = 50) -> list[dict[str, Any]]:
    """Get recent runs, newest first."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(row) for row in rows]


def get_run_events(run_id: str) -> list[dict[str, Any]]:
    """Get all events for a specific run, ordered by timestamp."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM events WHERE run_id = ? ORDER BY id ASC", (run_id,)
    ).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        # Parse data back to dict
        try:
            d["data"] = json.loads(d["data"])
        except (json.JSONDecodeError, TypeError):
            pass
        result.append(d)
    return result
