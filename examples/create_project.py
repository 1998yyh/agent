"""创建项目示例"""

import asyncio
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent import Agent
from agents.tools.file_tools import FileReadTool, FileWriteTool
from tools.git_tool import GitTool
from tools.project_tool import ProjectTool
from utils.config import get_api_key


async def main():
    """创建项目示例"""
    # 设置 API 密钥
    os.environ["ANTHROPIC_API_KEY"] = get_api_key()

    # 创建项目目录
    project_dir = "./demo_project"

    print("创建 ProjectAgent...")
    agent = Agent(
        name="ProjectAgent",
        system="你是一个项目初始化助手。帮助用户创建项目结构和文件。",
        tools=[
            FileReadTool(),
            FileWriteTool(),
            GitTool(),
            ProjectTool(),
        ],
        verbose=True,
    )

    # 创建 Python 项目
    print(f"\n创建 Python 项目到 {project_dir}")
    print("-" * 40)

    response = await agent.run_async(
        f"请在 {project_dir} 目录创建一个 Python 项目，包含:"
        "1. main.py - Hello World 程序"
        "2. README.md - 项目说明"
        "3. requirements.txt - 依赖文件"
        "然后初始化 Git 仓库并提交"
    )

    # 显示结果
    print("\n结果:")
    for block in response.content:
        if block.type == "text":
            print(block.text)

    print("\n示例完成！")
    print(f"查看项目：cd {project_dir} && ls -la")


if __name__ == "__main__":
    asyncio.run(main())
