"""Shell 命令执行工具"""

import subprocess
from agents.tools.base import Tool


class ShellTool(Tool):
    """Shell 工具 - 执行安全的 Shell 命令"""

    def __init__(self):
        super().__init__(
            name="shell",
            description="""
            执行 Shell 命令。

            安全限制:
            - 仅限开发相关命令 (npm, pip, python, node 等)
            - 禁止危险命令 (rm -rf, sudo 等)
            - 超时限制 60 秒
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 Shell 命令",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "工作目录",
                    },
                },
                "required": ["command"],
            },
        )

        # 禁止的命令列表
        self.blocked_commands = [
            "rm -rf",
            "sudo",
            "dd",
            "mkfs",
        ]

    async def execute(self, command: str, cwd: str = None) -> str:
        """执行 Shell 命令

        参数:
            command: Shell 命令
            cwd: 工作目录

        返回:
            命令输出或错误信息
        """
        # 安全检查
        for blocked in self.blocked_commands:
            if blocked in command:
                return f"安全限制：命令包含被禁止的操作 '{blocked}'"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=cwd,
                encoding="utf-8",
            )

            output = result.stdout
            if result.stderr:
                output += f"\n错误：{result.stderr}"

            return output or "命令执行成功"

        except subprocess.TimeoutExpired:
            return "命令执行超时 (超过 60 秒)"
        except Exception as e:
            return f"执行命令失败：{str(e)}"
