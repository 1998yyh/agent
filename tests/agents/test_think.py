"""Think 工具单元测试"""

import pytest
from agents.tools.think import ThinkTool


class TestThinkTool:
    """ThinkTool 测试类"""

    def test_think_tool_init(self):
        """测试 ThinkTool 初始化"""
        tool = ThinkTool()

        assert tool.name == "think"
        assert "思考" in tool.description or "think" in tool.description.lower()
        assert "thought" in tool.input_schema["required"]

    def test_think_tool_execute(self):
        """测试执行思考工具"""
        tool = ThinkTool()

        import asyncio
        result = asyncio.run(tool.execute(thought="这是一个测试思考"))

        assert result == "思考完成！"
