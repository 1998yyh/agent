"""Observer WebSocket 服务器"""

import asyncio
import json
import logging
from typing import Any

import websockets
from websockets.asyncio.server import ServerConnection, serve

logger = logging.getLogger(__name__)


class ObserverServer:
    """WebSocket 服务器 - 广播事件给所有连接的客户端

    Attributes:
        host: 服务器监听地址
        port: 服务器端口
        clients: 已连接的客户端集合
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        """初始化服务器

        Args:
            host: 监听地址
            port: 监听端口
        """
        self.host = host
        self.port = port
        self.clients: set[ServerConnection] = set()
        self._server = None
        self._serve_task: asyncio.Task | None = None

    async def start(self):
        """启动服务器"""
        logger.info(f"Starting Observer Server on {self.host}:{self.port}")
        async with serve(self._handler, self.host, self.port):
            # 保持服务器运行
            await asyncio.Future()

    async def start_background(self):
        """在后台启动服务器

        Returns:
            asyncio.Task 服务器任务
        """
        self._serve_task = asyncio.create_task(self.start())
        await asyncio.sleep(0.5)  # 等待服务器启动
        return self._serve_task

    async def stop(self):
        """停止服务器"""
        # 关闭所有客户端连接
        for client in list(self.clients):
            await client.close()
        self.clients.clear()

        # 取消服务任务
        if self._serve_task:
            self._serve_task.cancel()
            try:
                await self._serve_task
            except asyncio.CancelledError:
                pass

    async def _handler(self, websocket: ServerConnection):
        """处理客户端连接

        Args:
            websocket: WebSocket 连接
        """
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")

        try:
            # 保持连接，接收但不处理客户端消息
            async for message in websocket:
                pass
        except websockets.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def broadcast(self, event: dict[str, Any]):
        """广播事件给所有客户端

        Args:
            event: 事件字典
        """
        if not self.clients:
            return

        message = json.dumps(event, ensure_ascii=False)
        # 异步发送给所有客户端，忽略失败的发送
        await asyncio.gather(
            *[client.send(message) for client in self.clients],
            return_exceptions=True
        )

    @property
    def client_count(self) -> int:
        """获取已连接客户端数量"""
        return len(self.clients)
