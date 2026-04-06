"""ObserverHook - 注入到 Agent 中捕获事件"""

import asyncio
from typing import Any

from .events import Event, EventType
from .logger import JSONLogger
from .server_client import WebSocketClient


class ObserverHook:
    """观察者钩子 - 注入到 Agent 中捕获并转发事件

    该类提供一系列回调方法，在 Agent 执行的关键节点被调用，
    将事件转发到 Logger(持久化) 和 WebSocket Server(实时广播)。

    Attributes:
        session_id: 会话标识符
        logger: JSON 日志记录器
        server_client: WebSocket 客户端
    """

    def __init__(
        self,
        session_id: str,
        logger: JSONLogger,
        server_client: WebSocketClient | None = None,
        server_url: str = "ws://127.0.0.1:8765"
    ):
        """初始化 ObserverHook

        Args:
            session_id: 会话唯一标识符
            logger: JSON 日志记录器
            server_client: 可选的 WebSocket 客户端实例，不提供则自动创建
            server_url: WebSocket 服务器地址 (仅在自动创建客户端时使用)
        """
        self.session_id = session_id
        self.logger = logger
        self.server_client = server_client
        self._server_url = server_url
        self._owns_client = server_client is None

    async def _ensure_client_connected(self):
        """确保 WebSocket 客户端已连接"""
        if self.server_client and not self.server_client.is_connected:
            try:
                await self.server_client.connect()
            except Exception:
                # 连接失败时静默处理，仅使用本地日志
                pass

    async def _emit(self, event: Event):
        """发送事件到 Logger 和 Server

        Args:
            event: 要发送的事件
        """
        # 记录到本地日志 (总是执行)
        await self.logger.log(event)

        # 发送到服务器 (如果可用)
        if self.server_client:
            try:
                await self._ensure_client_connected()
                if self.server_client.is_connected:
                    await self.server_client.send(event.to_dict())
            except Exception:
                # 发送失败时静默处理
                pass

    async def on_session_start(self, model: str, tools: list[str]):
        """会话开始事件

        Args:
            model: 使用的模型名称
            tools: 可用工具列表
        """
        event = Event(
            event_type=EventType.SESSION_START,
            session_id=self.session_id,
            data={"model": model, "tools": tools}
        )
        await self._emit(event)

    async def on_user_message(self, content: str):
        """用户提问事件

        Args:
            content: 用户输入内容
        """
        event = Event(
            event_type=EventType.USER_MESSAGE,
            session_id=self.session_id,
            data={"content": content}
        )
        await self._emit(event)

    async def on_tool_call(self, name: str, input: dict[str, Any], tool_id: str):
        """工具调用事件

        Args:
            name: 工具名称
            input: 工具输入参数
            tool_id: 工具调用唯一标识符
        """
        event = Event(
            event_type=EventType.TOOL_CALL,
            session_id=self.session_id,
            data={"name": name, "input": input, "id": tool_id}
        )
        await self._emit(event)

    async def on_tool_result(self, name: str, result: str, tool_id: str):
        """工具结果事件

        Args:
            name: 工具名称
            result: 工具执行结果
            tool_id: 工具调用唯一标识符
        """
        event = Event(
            event_type=EventType.TOOL_RESULT,
            session_id=self.session_id,
            data={"name": name, "result": result, "id": tool_id}
        )
        await self._emit(event)

    async def on_ai_thinking(self, content: str):
        """AI 思考事件

        Args:
            content: 思考内容
        """
        event = Event(
            event_type=EventType.AI_THINKING,
            session_id=self.session_id,
            data={"content": content}
        )
        await self._emit(event)

    async def on_api_call(self, model: str, max_tokens: int):
        """API 调用事件

        Args:
            model: 使用的模型名称
            max_tokens: 最大 token 数
        """
        event = Event(
            event_type=EventType.API_CALL,
            session_id=self.session_id,
            data={"model": model, "max_tokens": max_tokens}
        )
        await self._emit(event)

    async def on_api_response(self, usage: dict[str, int], content: list):
        """API 响应事件

        Args:
            usage: Token 使用统计
            content: 响应内容
        """
        event = Event(
            event_type=EventType.API_RESPONSE,
            session_id=self.session_id,
            data={"usage": usage, "content": content}
        )
        await self._emit(event)

    async def on_ai_response(self, content: str, usage: dict[str, int]):
        """AI 最终响应事件

        Args:
            content: AI 回答内容
            usage: Token 使用统计
        """
        event = Event(
            event_type=EventType.AI_RESPONSE,
            session_id=self.session_id,
            data={"content": content, "usage": usage}
        )
        await self._emit(event)

    async def on_session_end(self, total_tokens: int, duration: float):
        """会话结束事件

        Args:
            total_tokens: 总 token 使用量
            duration: 会话持续时间 (秒)
        """
        event = Event(
            event_type=EventType.SESSION_END,
            session_id=self.session_id,
            data={"total_tokens": total_tokens, "duration": duration}
        )
        await self._emit(event)
        # 保存日志到文件
        self.logger.save()

    async def close(self):
        """关闭钩子，清理资源"""
        if self._owns_client and self.server_client:
            await self.server_client.disconnect()
