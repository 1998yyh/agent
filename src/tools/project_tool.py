"""项目生成工具"""

import os
from pathlib import Path
from agents.tools.base import Tool


class ProjectTool(Tool):
    """项目生成工具 - 创建项目结构"""

    def __init__(self):
        super().__init__(
            name="project",
            description="""
            创建项目结构和文件。

            操作:
            - create_dir: 创建目录
            - create_file: 创建文件
            - list_template: 列出可用模板
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "操作类型",
                        "enum": ["create_dir", "create_file", "list_template"],
                    },
                    "path": {
                        "type": "string",
                        "description": "路径",
                    },
                    "content": {
                        "type": "string",
                        "description": "文件内容 (create_file 需要)",
                    },
                },
                "required": ["operation", "path"],
            },
        )

    async def execute(
        self,
        operation: str,
        path: str,
        content: str = "",
    ) -> str:
        """执行项目操作

        参数:
            operation: 操作类型
            path: 路径
            content: 文件内容

        返回:
            操作结果
        """
        try:
            if operation == "create_dir":
                return self._create_dir(path)
            elif operation == "create_file":
                return self._create_file(path, content)
            elif operation == "list_template":
                return self._list_template()
            else:
                return f"错误：未知操作 '{operation}'"
        except Exception as e:
            return f"执行失败：{str(e)}"

    def _create_dir(self, path: str) -> str:
        """创建目录"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return f"目录已创建：{path}"
        except Exception as e:
            return f"创建目录失败：{str(e)}"

    def _create_file(self, path: str, content: str) -> str:
        """创建文件"""
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"文件已创建：{path} ({len(content)} 字符)"
        except Exception as e:
            return f"创建文件失败：{str(e)}"

    def _list_template(self) -> str:
        """列出模板"""
        templates = [
            "python_package - Python 包模板",
            "nodejs_app - Node.js 应用模板",
            "react_app - React 应用模板",
        ]
        return "可用模板:\n" + "\n".join(f"  - {t}" for t in templates)
