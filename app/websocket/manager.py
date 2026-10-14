from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    def add(self, websocket: WebSocket):
        self.connections.append(websocket)

    def remove(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, data: dict):
        for websocket in list(self.connections):
            try:
                await websocket.send_json(data)
            except Exception:
                self.remove(websocket)


ws_manager = ConnectionManager()