"""WebSocket 客户端 - 连接 Observer 服务器"""

import asyncio
import json
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection


class WebSocketClient:
    """WebSocket 客户端 - 发送事件到服务器

    Attributes:
        server_url: WebSocket 服务器 URL
        connection: WebSocket 连接
    """

    def __init__(self, server_url: str = "ws://127.0.0.1:8765"):
        """初始化客户端

        Args:
            server_url: WebSocket 服务器地址
        """
        self.server_url = server_url
        self.connection: ClientConnection | None = None
        self._connected = False

    async def connect(self):
        """连接到服务器"""
        self.connection = await websockets.connect(self.server_url)
        self._connected = True

    async def disconnect(self):
        """断开连接"""
        if self.connection:
            await self.connection.close()
        self._connected = False

    async def send(self, event: dict[str, Any]):
        """发送事件到服务器

        Args:
            event: 事件字典

        Raises:
            ConnectionError: 当未连接时
        """
        if not self._connected:
            await self.connect()

        await self.connection.send(json.dumps(event, ensure_ascii=False))

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected and self.connection is not None
