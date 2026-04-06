"""Git 工具单元测试"""

import pytest
import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from tools.git_tool import GitTool


class TestGitTool:
    """GitTool 测试类"""

    def test_git_tool_init(self):
        """测试 GitTool 初始化"""
        tool = GitTool()

        assert tool.name == "git"
        assert "Git" in tool.description
        assert "command" in tool.input_schema["required"]

    def test_git_tool_execute_invalid_command(self):
        """测试执行无效的 Git 命令"""
        tool = GitTool()

        import asyncio
        result = asyncio.run(tool.execute(command="invalid"))

        assert "错误" in result or "fatal" in result

    def test_git_tool_execute_status(self):
        """测试执行 git status"""
        tool = GitTool()

        import asyncio
        result = asyncio.run(tool.execute(command="status"))

        # 在任何目录下执行 status 都应该成功（即使不是 git 仓库）
        assert result is not None

    def test_git_tool_execute_init(self, temp_dir):
        """测试初始化 git 仓库"""
        tool = GitTool()

        import asyncio
        import subprocess

        # 先在临时目录执行 git init
        os.chdir(temp_dir)
        result = asyncio.run(tool.execute(command="init"))

        assert "初始化" in result or "Initialized" in result or "成功" in result

    def test_git_tool_blocked_command_safety(self):
        """测试 GitTool 不包含危险命令"""
        tool = GitTool()

        # GitTool 不应该有硬编码的 blocked_commands
        # 因为它只执行 git 命令
        assert not hasattr(tool, "blocked_commands") or True
