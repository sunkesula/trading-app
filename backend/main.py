from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.api.sentiment import router as sentiment_router
from backend.api.subscriptions import router as subscriptions_router
from backend.api.tickers import router as tickers_router
from backend.scheduler.setup import create_scheduler
from backend.services.ws_manager import manager

logging.basicConfig(level=logging.INFO)

_scheduler = create_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _scheduler.start()
    yield
    _scheduler.shutdown(wait=False)


app = FastAPI(title="Trading App — Indicator Tracking", lifespan=lifespan)

app.include_router(tickers_router)
app.include_router(subscriptions_router)
app.include_router(sentiment_router)


@app.websocket("/ws/{symbol}")
async def websocket_symbol(websocket: WebSocket, symbol: str):
    """Client subscribes to live indicator updates for a specific symbol."""
    await manager.connect(websocket, symbol=symbol.upper())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, symbol=symbol.upper())


@app.websocket("/ws")
async def websocket_global(websocket: WebSocket):
    """Client receives all broadcast events (market sentiment, etc.)."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/health")
async def health():
    return {"status": "ok"}
