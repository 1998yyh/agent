"""Agent 基类和结果类"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from anthropic import Anthropic

if TYPE_CHECKING:
    from ..agents.tools.base import Tool
    from ..orchestrator.context_store import WorkflowContext

from ..utils.config import ModelConfig, get_model_config


@dataclass
class AgentResult:
    """Agent 执行结果

    Attributes:
        success: 是否成功
        output: 输出结果
        error: 错误信息
        context: 工作流上下文
        can_retry: 是否可重试
    """
    success: bool = True
    output: Any = None
    error: Optional[str] = None
    context: Optional["WorkflowContext"] = None
    can_retry: bool = False

    def __post_init__(self):
        if not self.success and not self.error:
            self.error = "未知错误"


class BaseAgent(ABC):
    """所有 Agent 的抽象基类

    Attributes:
        name: Agent 名称
        system_prompt: 系统提示词
        verbose: 是否启用详细日志
    """

    name: str
    system_prompt: str
    verbose: bool = True

    def __init__(
        self,
        name: str | None = None,
        system_prompt: str | None = None,
        verbose: bool = True,
        model_config: Optional[ModelConfig] = None,
    ):
        """初始化 BaseAgent

        Args:
            name: Agent 名称
            system_prompt: 系统提示词
            verbose: 是否启用详细日志
            model_config: 模型配置
        """
        if name:
            self.name = name
        if system_prompt:
            self.system_prompt = system_prompt
        self.verbose = verbose
        self.model_config = model_config or get_model_config()

    @abstractmethod
    async def execute(self, context: "WorkflowContext") -> AgentResult:
        """执行 Agent 任务（抽象方法）

        Args:
            context: 工作流上下文

        Returns:
            Agent 执行结果
        """
        pass

    def get_tools(self) -> list["Tool"]:
        """获取 Agent 可用工具

        Returns:
            工具列表
        """
        return []

    async def _call_llm(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list["Tool"]] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Any:
        """调用 Claude API

        Args:
            messages: 消息历史
            tools: 可用工具列表
            max_tokens: 最大 token 数
            model: 模型名称

        Returns:
            API 响应
        """
        client = Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            base_url=self.model_config.base_url,
        )

        params = {
            "model": model or self.model_config.model,
            "max_tokens": max_tokens or self.model_config.max_tokens,
            "system": self.system_prompt,
            "messages": messages,
        }

        if tools:
            params["tools"] = [tool.to_dict() for tool in tools]

        # 合并请求头
        default_headers = {"anthropic-beta": "code-execution-2025-05-22"}
        if "extra_headers" in params:
            custom_headers = params.pop("extra_headers")
            merged_headers = {**default_headers, **custom_headers}
        else:
            merged_headers = default_headers

        return client.messages.create(**params, extra_headers=merged_headers)

    def _extract_text_content(self, response: Any) -> str:
        """从响应中提取文本内容

        Args:
            response: API 响应

        Returns:
            文本内容
        """
        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
        return "".join(text_parts)
