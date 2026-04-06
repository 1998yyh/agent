"""工具模块单元测试"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from agents.tools.base import Tool


class TestTool:
    """Tool 基类测试"""

    def test_tool_has_required_attributes(self):
        """测试工具类有必需的属性"""
        # Tool 是 dataclass，需要通过子类实例化
        class TestToolImpl(Tool):
            async def execute(self, **kwargs):
                return "test"

        tool = TestToolImpl(name="test", description="test", input_schema={})

        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert hasattr(tool, "input_schema")

    def test_tool_to_dict(self):
        """测试工具转换为字典"""
        class TestToolImpl(Tool):
            async def execute(self, **kwargs):
                return "test"

        tool = TestToolImpl(
            name="test_tool",
            description="测试工具",
            input_schema={"type": "object"}
        )

        result = tool.to_dict()

        assert result["name"] == "test_tool"
        assert result["description"] == "测试工具"
        assert result["input_schema"] == {"type": "object"}

    def test_tool_execute_not_implemented(self):
        """测试基类 execute 方法抛出异常"""
        class TestToolImpl(Tool):
            pass

        tool = TestToolImpl(name="test", description="test", input_schema={})

        with pytest.raises(NotImplementedError):
            import asyncio
            asyncio.run(tool.execute())
