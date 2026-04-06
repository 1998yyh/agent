"""Shell 工具单元测试"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from tools.shell_tool import ShellTool


class TestShellTool:
    """ShellTool 测试类"""

    def test_shell_tool_init(self):
        """测试 ShellTool 初始化"""
        tool = ShellTool()

        assert tool.name == "shell"
        assert "Shell" in tool.description
        assert "command" in tool.input_schema["required"]
        assert hasattr(tool, "blocked_commands")

    def test_shell_tool_blocked_commands(self):
        """测试 ShellTool 阻止危险命令"""
        tool = ShellTool()

        blocked = [
            "rm -rf",
            "sudo",
            "dd",
            "mkfs",
        ]

        for cmd in blocked:
            assert cmd in tool.blocked_commands

    def test_shell_tool_execute_blocked(self):
        """测试执行被阻止的命令"""
        tool = ShellTool()

        import asyncio
        result = asyncio.run(tool.execute(command="sudo rm -rf /"))

        assert "安全限制" in result or "禁止" in result

    def test_shell_tool_execute_safe_command(self):
        """测试执行安全命令"""
        tool = ShellTool()

        import asyncio

        # 执行一个安全的命令（在 Windows 上使用 dir，Linux 上使用 ls）
        import os
        cmd = "dir" if os.name == "nt" else "ls"

        result = asyncio.run(tool.execute(command=cmd))

        # 命令应该执行（可能成功或在某些环境下失败，但不应该被阻止）
        assert "安全限制" not in result

    def test_shell_tool_execute_with_cwd(self, temp_dir):
        """测试在指定工作目录执行命令"""
        tool = ShellTool()

        import asyncio

        result = asyncio.run(tool.execute(command="pwd", cwd=temp_dir))

        # 命令应该执行
        assert result is not None
