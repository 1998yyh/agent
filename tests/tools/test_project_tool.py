"""项目工具单元测试"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from tools.project_tool import ProjectTool


class TestProjectTool:
    """ProjectTool 测试类"""

    def test_project_tool_init(self):
        """测试 ProjectTool 初始化"""
        tool = ProjectTool()

        assert tool.name == "project"
        assert "项目" in tool.description or "Project" in tool.description
        assert "operation" in tool.input_schema["required"]
        assert "path" in tool.input_schema["required"]

    def test_project_tool_create_dir(self, temp_dir):
        """测试创建目录"""
        tool = ProjectTool()

        import asyncio
        new_dir = os.path.join(temp_dir, "test_dir")
        result = asyncio.run(tool.execute(operation="create_dir", path=new_dir))

        assert os.path.isdir(new_dir)
        assert "创建" in result or "成功" in result

    def test_project_tool_create_file(self, temp_dir):
        """测试创建文件"""
        tool = ProjectTool()

        import asyncio
        new_file = os.path.join(temp_dir, "test.txt")
        content = "测试内容"
        result = asyncio.run(tool.execute(
            operation="create_file",
            path=new_file,
            content=content
        ))

        assert os.path.isfile(new_file)
        with open(new_file, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_project_tool_list_template(self):
        """测试列出模板"""
        tool = ProjectTool()

        import asyncio
        result = asyncio.run(tool.execute(operation="list_template", path=""))

        assert "python_package" in result
        assert "nodejs_app" in result
        assert "react_app" in result

    def test_project_tool_invalid_operation(self):
        """测试无效操作"""
        tool = ProjectTool()

        import asyncio
        result = asyncio.run(tool.execute(operation="invalid", path=""))

        assert "错误" in result or "未知" in result
