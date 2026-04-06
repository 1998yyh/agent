"""Git 版本控制工具"""

import subprocess
from agents.tools.base import Tool


class GitTool(Tool):
    """Git 工具 - 执行常见 Git 操作"""

    def __init__(self):
        super().__init__(
            name="git",
            description="""
            执行 Git 版本控制操作。

            支持的命令:
            - init: 初始化仓库
            - add: 添加文件
            - commit: 提交更改
            - status: 查看状态
            - log: 查看历史
            - branch: 分支管理
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Git 命令",
                        "enum": ["init", "add", "commit", "status", "log", "branch"],
                    },
                    "args": {
                        "type": "string",
                        "description": "命令参数",
                    },
                    "message": {
                        "type": "string",
                        "description": "提交消息 (commit 命令需要)",
                    },
                },
                "required": ["command"],
            },
        )

    async def execute(
        self,
        command: str,
        args: str = "",
        message: str = "",
    ) -> str:
        """执行 Git 命令

        参数:
            command: Git 命令
            args: 命令参数
            message: 提交消息

        返回:
            命令输出或错误信息
        """
        try:
            cmd = ["git", command]

            if args:
                cmd.extend(args.split())

            if command == "commit" and message:
                cmd.extend(["-m", message])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
            )

            if result.returncode == 0:
                return result.stdout or "命令执行成功"
            else:
                return f"Git 错误：{result.stderr}"

        except subprocess.TimeoutExpired:
            return "Git 命令超时 (超过 30 秒)"
        except Exception as e:
            return f"执行 Git 命令失败：{str(e)}"
