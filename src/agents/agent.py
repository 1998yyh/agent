"""Agent 实现 - 基于 Claude API 和工具系统"""

import asyncio
import os
from contextlib import AsyncExitStack
from typing import Any

from anthropic import Anthropic

from utils.config import ModelConfig  # 统一模型配置
from .tools.base import Tool  # 工具基类
from .utils.connections import setup_mcp_connections  # MCP 连接设置
from .utils.history_util import MessageHistory  # 消息历史管理
from .utils.tool_util import execute_tools  # 工具执行


class Agent:
    """基于 Claude 的 Agent 类，支持工具调用"""

    def __init__(
        self,
        name: str,
        system: str,
        tools: list[Tool] | None = None,
        mcp_servers: list[dict[str, Any]] | None = None,
        config: ModelConfig | None = None,
        verbose: bool = False,
        client: Anthropic | None = None,
        message_params: dict[str, Any] | None = None,
        observer_hook: Any | None = None,  # ObserverHook 实例，用于实时监控
    ):
        """初始化 Agent

        参数:
            name: Agent 标识符，用于日志
            system: Agent 的系统提示词
            tools: Agent 可使用的工具列表
            mcp_servers: MCP (Model Context Protocol) 服务器配置
            config: 模型配置，包含默认参数
            verbose: 启用详细日志输出
            client: Anthropic 客户端实例
            message_params: client.messages.create() 的额外参数，
                           会覆盖 config 中冲突的参数
            observer_hook: ObserverHook 实例，用于实时监控 Agent 执行
        """
        self.name = name  # Agent 名称
        self.system = system  # 系统提示词
        self.verbose = verbose  # 是否启用详细日志
        self.tools = list(tools or [])  # 工具列表
        self.config = config or ModelConfig()  # 模型配置
        self.mcp_servers = mcp_servers or []  # MCP 服务器配置
        self.message_params = message_params or {}  # 额外消息参数
        self.observer_hook = observer_hook  # ObserverHook 实例
        self.client = client or Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            base_url=self.config.base_url,
        )  # Anthropic 客户端
        self.history = MessageHistory(
            model=self.config.model,
            system=self.system,
            context_window_tokens=self.config.context_window_tokens,
            client=self.client,
        )  # 消息历史管理器

        if self.verbose:
            print(f"\n[{self.name}] Agent initialized")

    def _prepare_message_params(self) -> dict[str, Any]:
        """准备 client.messages.create() 调用所需的参数

        返回包含 config 基础参数的字典，
        message_params 会覆盖其中冲突的键
        """
        return {
            "model": self.config.model,  # 模型名称
            "max_tokens": self.config.max_tokens,  # 最大 token 数
            "temperature": self.config.temperature,  # 温度参数
            "system": self.system,  # 系统提示词
            "messages": self.history.format_for_api(),  # 格式化的消息历史
            "tools": [tool.to_dict() for tool in self.tools],  # 工具定义列表
            **self.message_params,  # 额外参数
        }

    async def _agent_loop(self, user_input: str) -> list[dict[str, Any]]:
        """处理用户输入并在循环中处理工具调用"""
        if self.verbose:
            print(f"\n[{self.name}] Received: {user_input}")

        # 发送用户消息事件
        if self.observer_hook:
            await self.observer_hook.on_user_message(user_input)

        await self.history.add_message("user", user_input, None)

        tool_dict = {tool.name: tool for tool in self.tools}  # 工具字典

        while True:
            self.history.truncate()  # 截断超出上下文窗口的历史
            params = self._prepare_message_params()

            # 发送 API 调用事件
            if self.observer_hook:
                await self.observer_hook.on_api_call(
                    self.config.model,
                    self.config.max_tokens
                )

            # 合并请求头 - 默认的 beta 头可以被 message_params 覆盖
            default_headers = {"anthropic-beta": "code-execution-2025-05-22"}
            if "extra_headers" in params:
                # 从 params 中弹出 extra_headers 并与默认值合并
                custom_headers = params.pop("extra_headers")
                merged_headers = {**default_headers, **custom_headers}
            else:
                merged_headers = default_headers

            response = self.client.messages.create(
                **params,
                extra_headers=merged_headers
            )

            # 发送 API 响应事件
            if self.observer_hook:
                await self.observer_hook.on_api_response(
                    dict(response.usage) if hasattr(response, "usage") else {},
                    [block.to_dict() if hasattr(block, "to_dict") else block for block in response.content]
                )

            # 提取工具调用块
            tool_calls = [
                block for block in response.content if block.type == "tool_use"
            ]

            if self.verbose:
                for block in response.content:
                    if block.type == "text":
                        print(f"\n[{self.name}] Output: {block.text}")
                    elif block.type == "tool_use":
                        params_str = ", ".join(
                            [f"{k}={v}" for k, v in block.input.items()]
                        )
                        print(
                            f"\n[{self.name}] Tool call: "
                            f"{block.name}({params_str})"
                        )

            await self.history.add_message(
                "assistant", response.content, response.usage
            )

            if tool_calls:
                # 发送工具调用事件
                if self.observer_hook:
                    for tool_call in tool_calls:
                        await self.observer_hook.on_tool_call(
                            tool_call.name,
                            tool_call.input,
                            tool_call.id
                        )

                # 执行工具调用
                tool_results = await execute_tools(
                    tool_calls,
                    tool_dict,
                )

                # 发送工具结果事件
                if self.observer_hook:
                    for block in tool_results:
                        await self.observer_hook.on_tool_result(
                            block.get("name", ""),
                            block.get("content", ""),
                            block.get("tool_use_id", "")
                        )

                if self.verbose:
                    for block in tool_results:
                        print(
                            f"\n[{self.name}] Tool result: "
                            f"{block.get('content')}"
                        )
                await self.history.add_message("user", tool_results)
            else:
                # 发送 AI 响应事件
                if self.observer_hook:
                    text_content = ""
                    for block in response.content:
                        if block.type == "text":
                            text_content += block.text
                        elif hasattr(block, "text") and block.type == "thinking":
                            # 发送思考事件
                            await self.observer_hook.on_ai_thinking(block.text)

                    await self.observer_hook.on_ai_response(
                        text_content,
                        dict(response.usage) if hasattr(response, "usage") else {}
                    )
                return response  # 没有工具调用，返回最终响应

    async def run_async(self, user_input: str) -> list[dict[str, Any]]:
        """异步运行 Agent，支持 MCP 工具"""
        async with AsyncExitStack() as stack:
            original_tools = list(self.tools)

            try:
                # 设置 MCP 连接并获取 MCP 工具
                mcp_tools = await setup_mcp_connections(
                    self.mcp_servers, stack
                )
                self.tools.extend(mcp_tools)  # 添加 MCP 工具到工具列表
                return await self._agent_loop(user_input)
            finally:
                self.tools = original_tools  # 恢复原始工具列表

    def run(self, user_input: str) -> list[dict[str, Any]]:
        """同步运行 Agent"""
        return asyncio.run(self.run_async(user_input))
