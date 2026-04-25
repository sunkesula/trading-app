from __future__ import annotations

import json
from collections import defaultdict
from typing import Optional

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._symbol_connections: dict = defaultdict(list)
        self._all_connections: list = []

    async def connect(self, websocket: WebSocket, symbol: Optional[str] = None) -> None:
        await websocket.accept()
        self._all_connections.append(websocket)
        if symbol:
            self._symbol_connections[symbol].append(websocket)

    def disconnect(self, websocket: WebSocket, symbol: Optional[str] = None) -> None:
        if websocket in self._all_connections:
            self._all_connections.remove(websocket)
        if symbol and websocket in self._symbol_connections[symbol]:
            self._symbol_connections[symbol].remove(websocket)

    async def broadcast_symbol(self, symbol: str, payload: dict) -> None:
        """Push a message to all clients subscribed to a specific symbol."""
        message = json.dumps(payload)
        dead = []
        for ws in self._symbol_connections.get(symbol, []):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, symbol)

    async def broadcast_all(self, payload: dict) -> None:
        """Push a message to all connected clients (e.g. market sentiment updates)."""
        message = json.dumps(payload)
        dead = []
        for ws in self._all_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()
