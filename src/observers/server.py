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

        # 创建服务器
        async with serve(self._handler, self.host, self.port) as server:
            logger.info(f"Server listening on {self.host}:{self.port}")
            # 保持服务器运行直到被取消
            while True:
                await asyncio.sleep(1)

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
        # 关闭服务器
        if self._server:
            self._server.close()

        # 等待服务器关闭
        if self._serve_task and not self._serve_task.done():
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
        print(f"[Observer Server] 客户端已连接，当前连接数：{len(self.clients)}")

        try:
            # 接收消息并广播给其他客户端
            async for message in websocket:
                logger.info(f"Received message from client, broadcasting to {len(self.clients) - 1} other clients")
                print(f"[Observer Server] 收到消息，正在广播给 {len(self.clients) - 1} 个客户端")
                await self.broadcast_to_others(message, websocket)
        except websockets.ConnectionClosed:
            logger.info("Client connection closed")
            print(f"[Observer Server] 客户端断开连接")
        finally:
            self.clients.discard(websocket)
            logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
            print(f"[Observer Server] 客户端已断开，当前连接数：{len(self.clients)}")

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

    async def broadcast_to_others(self, message: str, sender: ServerConnection):
        """广播消息给除发送者外的所有客户端

        Args:
            message: 消息字符串
            sender: 发送者客户端连接
        """
        other_clients = [c for c in self.clients if c != sender]
        if not other_clients:
            return

        await asyncio.gather(
            *[client.send(message) for client in other_clients],
            return_exceptions=True
        )

    @property
    def client_count(self) -> int:
        """获取已连接客户端数量"""
        return len(self.clients)
