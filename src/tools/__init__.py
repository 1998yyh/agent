"""工具模块"""

# 重导出 agents.tools 中的工具
import sys
from pathlib import Path

# 将 agents.tools 的内容导入到 tools 命名空间
agents_tools_path = Path(__file__).parent.parent / "agents" / "tools"
sys.path.insert(0, str(agents_tools_path.parent.parent))

from agents.tools.base import Tool
from agents.tools.file_tools import FileReadTool, FileWriteTool
from .git_tool import GitTool
from .shell_tool import ShellTool
from .project_tool import ProjectTool

__all__ = [
    "Tool",
    "FileReadTool",
    "FileWriteTool",
    "GitTool",
    "ShellTool",
    "ProjectTool",
]
