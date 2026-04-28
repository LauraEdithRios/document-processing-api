import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WSManager:
    def __init__(self):
        self._connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, process_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[process_id].append(ws)

    async def disconnect(self, process_id: str, ws: WebSocket) -> None:
        conns = self._connections.get(process_id, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            self._connections.pop(process_id, None)

    async def broadcast(self, process_id: str, data: dict) -> None:
        conns = list(self._connections.get(process_id, []))
        dead = []
        for ws in conns:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(process_id, ws)

    def broadcast_from_thread(self, process_id: str, data: dict) -> None:
        """Called from worker threads — schedules the coroutine on the main event loop."""
        if not self._loop or not self._connections.get(process_id):
            return
        asyncio.run_coroutine_threadsafe(
            self.broadcast(process_id, data),
            self._loop,
        )

manager = WSManager()
