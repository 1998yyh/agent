"""文件工具单元测试"""

import pytest
import os
import tempfile
from agents.tools.file_tools import FileReadTool, FileWriteTool


class TestFileReadTool:
    """FileReadTool 测试类"""

    def test_file_read_tool_init(self):
        """测试 FileReadTool 初始化"""
        tool = FileReadTool()

        assert tool.name == "file_read"
        assert "operation" in tool.input_schema["required"]
        assert "path" in tool.input_schema["required"]

    def test_file_read_tool_read_nonexistent_file(self):
        """测试读取不存在的文件"""
        tool = FileReadTool()

        import asyncio
        result = asyncio.run(tool.execute(operation="read", path="/nonexistent/file.txt"))

        assert "错误" in result

    def test_file_read_tool_list_nonexistent_dir(self):
        """测试列出不存在的目录"""
        tool = FileReadTool()

        import asyncio
        result = asyncio.run(tool.execute(operation="list", path="/nonexistent/dir"))

        assert "错误" in result

    def test_file_read_tool_read_file(self, temp_dir):
        """测试读取文件"""
        tool = FileReadTool()

        # 先创建文件
        file_path = os.path.join(temp_dir, "test.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("测试内容")

        import asyncio
        result = asyncio.run(tool.execute(operation="read", path=file_path))

        assert "测试内容" in result

    def test_file_read_tool_list_dir(self, temp_dir):
        """测试列出目录"""
        tool = FileReadTool()

        # 先创建文件
        file_path = os.path.join(temp_dir, "test.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("测试内容")

        import asyncio
        result = asyncio.run(tool.execute(operation="list", path=temp_dir))

        assert "test.txt" in result


class TestFileWriteTool:
    """FileWriteTool 测试类"""

    def test_file_write_tool_init(self):
        """测试 FileWriteTool 初始化"""
        tool = FileWriteTool()

        assert tool.name == "file_write"
        assert "operation" in tool.input_schema["required"]
        assert "path" in tool.input_schema["required"]

    def test_file_write_tool_write_file(self, temp_dir):
        """测试写入文件"""
        tool = FileWriteTool()

        import asyncio
        file_path = os.path.join(temp_dir, "test.txt")
        content = "测试内容"
        result = asyncio.run(tool.execute(
            operation="write",
            path=file_path,
            content=content
        ))

        assert os.path.isfile(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_file_write_tool_write_without_content(self):
        """测试没有 content 时写入文件"""
        tool = FileWriteTool()

        import asyncio
        result = asyncio.run(tool.execute(
            operation="write",
            path="/tmp/test.txt"
        ))

        assert "错误" in result

    def test_file_write_tool_edit_nonexistent_file(self):
        """测试编辑不存在的文件"""
        tool = FileWriteTool()

        import asyncio
        result = asyncio.run(tool.execute(
            operation="edit",
            path="/nonexistent/file.txt",
            old_text="old",
            new_text="new"
        ))

        assert "错误" in result

    def test_file_write_tool_edit_file(self, temp_dir):
        """测试编辑文件"""
        tool = FileWriteTool()

        # 先创建文件
        file_path = os.path.join(temp_dir, "test.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("旧内容")

        import asyncio
        result = asyncio.run(tool.execute(
            operation="edit",
            path=file_path,
            old_text="旧内容",
            new_text="新内容"
        ))

        with open(file_path, "r", encoding="utf-8") as f:
            assert f.read() == "新内容"
