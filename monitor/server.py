"""Agent Monitor — FastAPI server with WebSocket support.

Endpoints:
- WS  /ws/push   — Agent-facing: agents push events here
- WS  /ws/live   — Browser-facing: UI receives real-time event broadcast
- GET /api/runs  — List historical runs
- GET /api/runs/{run_id} — Get all events for a run
- GET /          — Serve the dashboard UI
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from db import init_db, store_event, get_runs, get_run_events

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("monitor")

app = FastAPI(title="dbt Agent Monitor")

# Track connected browser clients
_browser_clients: set[WebSocket] = set()


@app.on_event("startup")
async def startup() -> None:
    init_db()
    logger.info("Monitor server started — database initialized")


# ── Agent-facing WebSocket (receives events) ──────────────────────────
@app.websocket("/ws/push")
async def ws_push(websocket: WebSocket) -> None:
    """Accept events from agent containers."""
    await websocket.accept()
    remote = websocket.client
    logger.info("Agent connected: %s", remote)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from agent: %s", raw[:200])
                continue

            # Store in SQLite
            try:
                store_event(event)
            except Exception as exc:
                logger.error("Failed to store event: %s", exc)

            # Broadcast to all browser clients
            await _broadcast(raw)

    except WebSocketDisconnect:
        logger.info("Agent disconnected: %s", remote)
    except Exception as exc:
        logger.error("Agent WebSocket error: %s", exc)


# ── Browser-facing WebSocket (broadcasts events) ─────────────────────
@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket) -> None:
    """Stream live events to browser clients."""
    await websocket.accept()
    _browser_clients.add(websocket)
    logger.info("Browser client connected (%d total)", len(_browser_clients))

    try:
        # Keep the connection alive; browser may send subscribe messages
        while True:
            # We don't expect meaningful messages from the browser,
            # but we need to keep reading to detect disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        _browser_clients.discard(websocket)
        logger.info("Browser client disconnected (%d remaining)", len(_browser_clients))


async def _broadcast(message: str) -> None:
    """Send a message to all connected browser clients."""
    dead: list[WebSocket] = []
    for ws in _browser_clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _browser_clients.discard(ws)


# ── REST API ──────────────────────────────────────────────────────────
@app.get("/api/runs")
async def api_runs() -> JSONResponse:
    """List recent runs."""
    runs = get_runs()
    return JSONResponse(content=runs)


@app.get("/api/runs/{run_id}")
async def api_run_events(run_id: str) -> JSONResponse:
    """Get all events for a specific run."""
    events = get_run_events(run_id)
    return JSONResponse(content=events)


# ── Static files (serve UI) ──────────────────────────────────────────
# Mount AFTER API routes so /api/* takes precedence
app.mount("/", StaticFiles(directory="static", html=True), name="static")
