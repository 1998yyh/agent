"""与 MCP 服务器交互的工具"""

from typing import Any
from .base import Tool
from ..utils.connections import MCPConnection


class MCPTool(Tool):
    """MCP 工具类，用于连接 MCP 服务器"""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        connection: "MCPConnection",
    ):
        """初始化 MCP 工具

        参数:
            name: 工具名称
            description: 工具描述
            input_schema: 输入模式定义
            connection: MCP 连接对象
        """
        super().__init__(
            name=name, description=description, input_schema=input_schema
        )
        self.connection = connection  # MCP 连接

    async def execute(self, **kwargs) -> str:
        """使用给定的输入模式执行 MCP 工具

        注意：目前仅支持来自 MCP 工具的文本结果
        """
        try:
            result = await self.connection.call_tool(
                self.name, arguments=kwargs
            )

            # 提取文本内容
            if hasattr(result, "content") and result.content:
                for item in result.content:
                    if getattr(item, "type", None) == "text":
                        return item.text

            return "工具响应中无文本内容"
        except Exception as e:
            return f"错误：执行 {self.name} 失败：{e}"
