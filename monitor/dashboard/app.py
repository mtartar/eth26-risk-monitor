"""FastAPI dashboard: live positions, alert history, and an NL query box.

WebSocket clients receive a JSON message on every real risk transition,
pushed by the running Pipeline's on_transition callback — real-time, not
polling. REST endpoints expose a point-in-time snapshot and the NL query
layer for anything that doesn't want a WebSocket connection (e.g. curl).
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from monitor.ai.query import answer_position_query
from monitor.observability.cost_tracker import cost_tracker
from monitor.observability.logging_config import configure_logging
from monitor.pipeline import Pipeline
from monitor.scoring.risk_state import RiskTransition

configure_logging()
logger = logging.getLogger("monitor.dashboard")

_STATIC_DIR = Path(__file__).parent / "static"
_websocket_clients: set[WebSocket] = set()
_pipeline_holder: dict[str, Pipeline] = {}


async def _broadcast(transition: RiskTransition, explanation: str | None) -> None:
    """Push one transition to every connected WebSocket client, dropping dead ones."""
    payload: dict[str, Any] = {
        "user_address": transition.user_address,
        "from_level": transition.from_level.value,
        "to_level": transition.to_level.value,
        "health_factor": transition.health_factor,
        "as_of_block": transition.as_of_block,
        "explanation": explanation,
    }
    dead = []
    for websocket in _websocket_clients:
        try:
            await websocket.send_json(payload)
        except Exception:
            dead.append(websocket)
    for websocket in dead:
        _websocket_clients.discard(websocket)


@asynccontextmanager
async def _lifespan(_: FastAPI):
    """Start the pipeline as a background task on app startup, cancel it on shutdown."""
    pipeline = Pipeline(on_transition=_broadcast)
    _pipeline_holder["pipeline"] = pipeline
    task = asyncio.create_task(pipeline.run())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="Risk Monitor Dashboard", lifespan=_lifespan)


def _pipeline() -> Pipeline:
    return _pipeline_holder["pipeline"]


@app.get("/")
async def index() -> FileResponse:
    """Serve the dashboard's single static HTML page."""
    return FileResponse(_STATIC_DIR / "index.html")


@app.get("/positions")
async def positions() -> list[dict]:
    """Return every tracked user's current health factor."""
    return _pipeline().tracked_positions()


class QueryRequest(BaseModel):
    """A natural-language question about tracked positions."""

    question: str


@app.post("/query")
async def query(request: QueryRequest) -> dict[str, str]:
    """Answer a plain-English question about tracked positions."""
    answer = answer_position_query(
        request.question,
        _pipeline().engine,
        as_of_block=0,
        as_of_timestamp=datetime.now(timezone.utc),
    )
    return {"answer": answer}


@app.get("/cost")
async def cost() -> dict[str, float | int]:
    """Real LLM token usage so far, and its estimated USD cost."""
    return {
        "input_tokens": cost_tracker.input_tokens,
        "output_tokens": cost_tracker.output_tokens,
        "call_count": cost_tracker.call_count,
        "estimated_usd": round(cost_tracker.estimated_usd, 6),
    }


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    """Prometheus scrape endpoint."""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    """Hold one live connection open, pushing risk transitions as they happen."""
    await websocket.accept()
    _websocket_clients.add(websocket)
    try:
        while True:
            # No client->server messages are expected; this just keeps the connection open.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _websocket_clients.discard(websocket)
