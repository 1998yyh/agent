"""Agent 框架的基础工具定义"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Tool:
    """所有 Agent 工具的基类"""

    name: str  # 工具名称
    description: str  # 工具描述
    input_schema: dict[str, Any]  # 输入模式定义（JSON Schema 格式）

    def to_dict(self) -> dict[str, Any]:
        """将工具转换为 Claude API 格式"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    async def execute(self, **kwargs) -> str:
        """使用提供的参数执行工具

        子类必须实现此方法
        """
        raise NotImplementedError(
            "Tool 子类必须实现 execute 方法"
        )
