"""文件操作工具 - 用于读取和写入文件"""

import asyncio
import glob
import os
from pathlib import Path

from .base import Tool


class FileReadTool(Tool):
    """用于读取文件和列出目录内容的工具"""

    def __init__(self):
        super().__init__(
            name="file_read",  # 工具名称：文件读取
            description="""
            读取文件或列出目录内容。

            支持的操作:
            - read: 读取文件内容
            - list: 列出目录中的文件
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "list"],
                        "description": "要执行的文件操作",
                    },
                    "path": {
                        "type": "string",
                        "description": "文件路径（读取操作）或目录路径（列出操作）",
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "最大读取行数（0 表示无限制）",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "文件匹配模式",
                    },
                },
                "required": ["operation", "path"],  # 必需参数
            },
        )

    async def execute(
        self,
        operation: str,
        path: str,
        max_lines: int = 0,
        pattern: str = "*",
    ) -> str:
        """执行文件读取操作

        参数:
            operation: 要执行的操作（read 或 list）
            path: 文件或目录路径
            max_lines: 最大读取行数（读取操作，0 表示无限制）
            pattern: 文件匹配模式（列出操作）

        返回:
            操作结果的字符串
        """
        if operation == "read":
            return await self._read_file(path, max_lines)
        elif operation == "list":
            return await self._list_files(path, pattern)
        else:
            return f"错误：不支持的操作 '{operation}'"

    async def _read_file(self, path: str, max_lines: int = 0) -> str:
        """从磁盘读取文件

        参数:
            path: 要读取的文件路径
            max_lines: 最大读取行数（0 表示读取整个文件）
        """
        try:
            file_path = Path(path)

            if not file_path.exists():
                return f"错误：文件不存在 {path}"
            if not file_path.is_file():
                return f"错误：{path} 不是文件"

            def read_sync():
                with open(file_path, encoding="utf-8", errors="replace") as f:
                    if max_lines > 0:
                        lines = []
                        for i, line in enumerate(f):
                            if i >= max_lines:
                                break
                            lines.append(line)
                        return "".join(lines)
                    return f.read()

            return await asyncio.to_thread(read_sync)
        except Exception as e:
            return f"错误：读取 {path} 失败：{str(e)}"

    async def _list_files(self, directory: str, pattern: str = "*") -> str:
        """列出目录中的文件"""
        try:
            dir_path = Path(directory)

            if not dir_path.exists():
                return f"错误：目录不存在 {directory}"
            if not dir_path.is_dir():
                return f"错误：{directory} 不是目录"

            def list_sync():
                search_pattern = os.path.join(directory, pattern)
                files = glob.glob(search_pattern)

                if not files:
                    return f"未找到匹配 {directory}/{pattern} 的文件"

                file_list = []
                for file_path in sorted(files):
                    path_obj = Path(file_path)
                    # 使用 Path.relative_to() 处理跨平台路径
                    try:
                        rel_path = str(path_obj.relative_to(dir_path))
                    except ValueError:
                        rel_path = str(file_path)

                    if path_obj.is_dir():
                        file_list.append(f"[DIR]  {rel_path}/")
                    else:
                        file_list.append(f"[FILE] {rel_path}")

                return "\n".join(file_list)

            return await asyncio.to_thread(list_sync)
        except Exception as e:
            return f"错误：列出 {directory} 失败：{str(e)}"


class FileWriteTool(Tool):
    """用于写入和编辑文件的工具"""

    def __init__(self):
        super().__init__(
            name="file_write",  # 工具名称：文件写入
            description="""
            写入或编辑文件。

            支持的操作:
            - write: 创建或完全替换文件
            - edit: 对文件的部分内容进行修改
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["write", "edit"],
                        "description": "要执行的文件操作",
                    },
                    "path": {
                        "type": "string",
                        "description": "要写入或编辑的文件路径",
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容",
                    },
                    "old_text": {
                        "type": "string",
                        "description": "要替换的文本（编辑操作）",
                    },
                    "new_text": {
                        "type": "string",
                        "description": "替换文本（编辑操作）",
                    },
                },
                "required": ["operation", "path"],  # 必需参数
            },
        )

    async def execute(
        self,
        operation: str,
        path: str,
        content: str = "",
        old_text: str = "",
        new_text: str = "",
    ) -> str:
        """执行文件写入操作

        参数:
            operation: 要执行的操作（write 或 edit）
            path: 文件路径
            content: 要写入的内容（写入操作）
            old_text: 要替换的文本（编辑操作）
            new_text: 替换文本（编辑操作）

        返回:
            操作结果的字符串
        """
        if operation == "write":
            if not content:
                return "错误：content 参数是必需的"
            return await self._write_file(path, content)
        elif operation == "edit":
            if not old_text or not new_text:
                return (
                    "错误：edit 操作需要同时提供 old_text 和 new_text 参数"
                )
            return await self._edit_file(path, old_text, new_text)
        else:
            return f"错误：不支持的操作 '{operation}'"

    async def _write_file(self, path: str, content: str) -> str:
        """将内容写入文件"""
        try:
            file_path = Path(path)
            os.makedirs(file_path.parent, exist_ok=True)  # 创建父目录

            def write_sync():
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return (
                    f"成功写入 {len(content)} 个字符到 {path}"
                )

            return await asyncio.to_thread(write_sync)
        except Exception as e:
            return f"错误：写入 {path} 失败：{str(e)}"

    async def _edit_file(self, path: str, old_text: str, new_text: str) -> str:
        """对文件进行针对性修改"""
        try:
            file_path = Path(path)

            if not file_path.exists():
                return f"错误：文件不存在 {path}"
            if not file_path.is_file():
                return f"错误：{path} 不是文件"

            def edit_sync():
                try:
                    with open(
                        file_path, encoding="utf-8", errors="replace"
                    ) as f:
                        content = f.read()

                    if old_text not in content:
                        return (
                            f"错误：在 {path} 中未找到指定的文本"
                        )

                    # 计算出现次数，警告多次匹配的情况
                    count = content.count(old_text)
                    if count > 1:
                        # 编辑并警告多次替换
                        new_content = content.replace(old_text, new_text)
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        return (
                            f"警告：找到 {count} 处匹配。"
                            f"已全部替换于 {path}"
                        )
                    else:
                        # 只有一处匹配，直接替换
                        new_content = content.replace(old_text, new_text)
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        return f"成功编辑 {path}"
                except UnicodeDecodeError:
                    return f"错误：{path} 似乎是二进制文件"

            return await asyncio.to_thread(edit_sync)
        except Exception as e:
            return f"错误：编辑 {path} 失败：{str(e)}"
