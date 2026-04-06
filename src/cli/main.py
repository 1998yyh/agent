"""DevAgent 命令行入口"""

import asyncio
import os
import sys
from datetime import datetime
import uuid

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from rich.console import Console
from rich.panel import Panel

from agents.agent import Agent
from agents.tools.think import ThinkTool
from agents.tools.file_tools import FileReadTool, FileWriteTool
from tools.git_tool import GitTool
from tools.shell_tool import ShellTool
from tools.project_tool import ProjectTool
from utils.config import get_api_key, ModelConfig, get_model_config, get_model_from_env, get_base_url_from_env

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """DevAgent - 多 Agent 软件开发系统"""
    pass


@cli.command()
@click.argument("request")
@click.option(
    "--workflow-id",
    "-w",
    help="恢复指定的工作流",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="启用详细输出",
)
@click.option(
    "--model",
    "-m",
    default=None,
    help="指定模型名称",
)
@click.option(
    "--base-url",
    "-b",
    default=None,
    help="指定 API 基础地址",
)
@click.option(
    "--observe",
    "-o",
    is_flag=True,
    help="启用 Observer 实时观察",
)
def run(request: str, workflow_id: str, verbose: bool, model: str, base_url: str, observe: bool):
    """运行新的工作流或恢复已有工作流"""
    try:
        api_key = get_api_key()
        os.environ["ANTHROPIC_API_KEY"] = api_key
    except ValueError as e:
        console.print(f"[red]错误：{e}[/red]")
        console.print("\n请设置环境变量:")
        console.print("  export ANTHROPIC_API_KEY='your-api-key'")
        console.print("\n或创建 .env 文件")
        return

    # 创建模型配置
    config = ModelConfig(
        model=model if model else get_model_from_env(),
        base_url=base_url if base_url else get_base_url_from_env(),
    ) if (model or base_url) else get_model_config()

    # 创建 ObserverHook (如果启用观察)
    observer_hook = None
    if observe:
        from observers.hook import ObserverHook
        from observers.logger import JSONLogger
        from observers.server_client import WebSocketClient

        session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        logger = JSONLogger()
        logger.start_session(session_id)
        client = WebSocketClient()
        observer_hook = ObserverHook(session_id=session_id, logger=logger, server_client=client)
        console.print(f"[green]Observer 已启动，会话 ID: {session_id}[/green]")

    agent = Agent(
        name="DevAgent",
        system="""你是一个专业的软件开发助手。你可以帮助用户:

1. 创建项目结构和初始化代码
2. 编写和修改代码文件
3. 执行 Git 版本控制操作
4. 运行开发命令和测试

请逐步思考每个任务，使用可用的工具来完成工作。
如果不确定，请先使用 think 工具进行推理。""",
        tools=[
            ThinkTool(),
            FileReadTool(),
            FileWriteTool(),
            GitTool(),
            ShellTool(),
            ProjectTool(),
        ],
        config=config,
        verbose=verbose,
        observer_hook=observer_hook,
    )

    console.print(Panel(f"用户需求：{request}", title="New Workflow"))

    async def execute():
        response = await agent.run_async(request)

        # 关闭 observer hook
        if observer_hook:
            await observer_hook.close()

        # 显示结果
        for block in response.content:
            if block.type == "text":
                console.print(f"\n{block.text}")

    asyncio.run(execute())


@cli.command()
@click.option(
    "--limit",
    "-l",
    default=10,
    help="显示最近的工作流数量",
)
def list_workflows(limit: int):
    """列出最近的工作流"""
    console.print("[yellow]工作流列表功能将在阶段 2 实现[/yellow]")


@cli.command()
@click.argument("workflow_id")
def status(workflow_id: str):
    """显示工作流状态"""
    console.print("[yellow]工作流状态功能将在阶段 2 实现[/yellow]")


@cli.command()
@click.option(
    "--model",
    "-m",
    default=None,
    help="指定模型名称",
)
@click.option(
    "--base-url",
    "-b",
    default=None,
    help="指定 API 基础地址",
)
@click.option(
    "--observe",
    "-o",
    is_flag=True,
    help="启用 Observer 实时观察",
)
def interactive(model: str, base_url: str, observe: bool):
    """进入交互模式"""
    console.print(Panel("DevAgent 交互模式", title="Welcome"))
    console.print("输入你的需求，输入 'quit' 退出\n")

    try:
        api_key = get_api_key()
        os.environ["ANTHROPIC_API_KEY"] = api_key
    except ValueError as e:
        console.print(f"[red]错误：{e}[/red]")
        return

    # 创建模型配置
    config = ModelConfig(
        model=model if model else get_model_from_env(),
        base_url=base_url if base_url else get_base_url_from_env(),
    ) if (model or base_url) else get_model_config()

    # 创建 ObserverHook (如果启用观察)
    observer_hook = None
    if observe:
        from observers.hook import ObserverHook
        from observers.logger import JSONLogger
        from observers.server_client import WebSocketClient

        session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        logger = JSONLogger()
        logger.start_session(session_id)
        client = WebSocketClient()
        observer_hook = ObserverHook(session_id=session_id, logger=logger, server_client=client)
        console.print(f"[green]Observer 已启动，会话 ID: {session_id}[/green]")

    agent = Agent(
        name="DevAgent",
        system="""你是一个专业的软件开发助手。你可以帮助用户:

1. 创建项目结构和初始化代码
2. 编写和修改代码文件
3. 执行 Git 版本控制操作
4. 运行开发命令和测试

请逐步思考每个任务，使用可用的工具来完成工作。
如果不确定，请先使用 think 工具进行推理。""",
        tools=[
            ThinkTool(),
            FileReadTool(),
            FileWriteTool(),
            GitTool(),
            ShellTool(),
            ProjectTool(),
        ],
        config=config,
        verbose=True,
        observer_hook=observer_hook,
    )

    while True:
        try:
            request = click.prompt("\n> ", prompt_suffix="")

            if request.lower() in ["quit", "exit", "q"]:
                # 关闭 observer hook
                if observer_hook:
                    asyncio.run(observer_hook.close())
                console.print("再见！")
                break

            if request.lower() == "help":
                print_help()
                continue

            # 执行工作流
            async def execute():
                response = await agent.run_async(request)
                # 每次执行后关闭 hook
                if observer_hook:
                    await observer_hook.close()
                for block in response.content:
                    if block.type == "text":
                        console.print(f"\n{block.text}")

            asyncio.run(execute())

        except KeyboardInterrupt:
            console.print("\n中断，继续输入以继续使用。")
        except Exception as e:
            console.print(f"\n发生错误：{str(e)}")


def print_help():
    """打印帮助信息"""
    console.print("""
交互模式帮助:
  - 输入需求，例如：'创建一个 Python 计算器项目'
  - 输入 'help' 显示此帮助
  - 输入 'quit' 退出

可用命令:
  dev-agent run <需求>     - 运行工作流
  dev-agent list           - 列出工作流
  dev-agent status <ID>    - 显示状态
  dev-agent interactive    - 交互模式
  dev-agent --help         - 显示帮助
""")


if __name__ == "__main__":
    cli()
