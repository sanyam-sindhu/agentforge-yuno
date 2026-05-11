from fastapi import WebSocket
from typing import Any
import json


class WebSocketManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active.remove(websocket)

    async def broadcast(self, event: str, data: Any):
        payload = json.dumps({"event": event, "data": data})
        for ws in list(self.active):
            try:
                await ws.send_text(payload)
            except Exception:
                self.active.remove(ws)


ws_manager = WebSocketManager()
