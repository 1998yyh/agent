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

        # 预连接 WebSocket 客户端 (使用持久事件循环)
        async def connect_observer():
            try:
                await client.connect()
                console.print(f"[green]Observer 已启动，会话 ID: {session_id}[/green]")
                console.print(f"[dim]已连接到 Observer 服务器：ws://127.0.0.1:8765[/dim]")
                console.print(f"[dim]请确保已运行 dev-agent watch 启动 Observer 服务器[/dim]")
            except Exception as e:
                console.print(f"[yellow]Observer 警告：无法连接到服务器：{e}[/yellow]")
                console.print(f"[dim]本地日志仍会保存到 storage/logs/{session_id}.json[/dim]")
                console.print(f"[dim]提示：请确保已运行 dev-agent watch 或 dev-agent observer-server[/dim]")

        # 在持久事件循环中连接
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(connect_observer())

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

    # 创建持久事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        async def execute():
            response = await agent.run_async(request)

            # 关闭 observer hook
            if observer_hook:
                await observer_hook.close()

            # 显示结果
            for block in response.content:
                if block.type == "text":
                    console.print(f"\n{block.text}")

        loop.run_until_complete(execute())
    finally:
        loop.close()


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

    # 创建持久事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

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

        # 预连接 WebSocket 客户端
        async def connect_observer_interactive():
            try:
                await client.connect()
                console.print(f"[green]Observer 已启动，会话 ID: {session_id}[/green]")
                console.print(f"[dim]已连接到 Observer 服务器：ws://127.0.0.1:8765[/dim]")
            except Exception as e:
                console.print(f"[yellow]Observer 警告：无法连接到服务器：{e}[/yellow]")
                console.print(f"[dim]本地日志仍会保存到 storage/logs/{session_id}.json[/dim]")
                console.print(f"[dim]提示：运行 dev-agent observer-server 启动服务器[/dim]")

        loop.run_until_complete(connect_observer_interactive())

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
                    loop.run_until_complete(observer_hook.close())
                console.print("再见！")
                break

            if request.lower() == "help":
                print_help()
                continue

            # 执行工作流 (使用持久事件循环)
            async def execute():
                response = await agent.run_async(request)
                # 注意：不在这里关闭 hook，以便继续使用同一个会话
                for block in response.content:
                    if block.type == "text":
                        console.print(f"\n{block.text}")

            loop.run_until_complete(execute())

        except KeyboardInterrupt:
            console.print("\n中断，继续输入以继续使用。")
        except Exception as e:
            console.print(f"\n发生错误：{str(e)}")

    # 清理事件循环
    loop.close()


def print_help():
    """打印帮助信息"""
    console.print("""
交互模式帮助:
  - 输入需求，例如：'创建一个 Python 计算器项目'
  - 输入 'help' 显示此帮助
  - 输入 'quit' 退出

可用命令:
  dev-agent watch          - 一键启动 Observer（推荐）
  dev-agent interactive    - 交互模式
  dev-agent interactive --observe  - 带 Observer 的交互模式
  dev-agent run <需求>     - 运行工作流
  dev-agent run --observe <需求>   - 带 Observer 的工作流
  dev-agent observer       - 仅启动 Observer 客户端
  dev-agent observer-server - 仅启动 Observer 服务器
  dev-agent replay         - 回放历史会话
  dev-agent --help         - 显示帮助
""")


@cli.command()
@click.option("--server", "-s", default="ws://127.0.0.1:8765", help="Observer 服务器地址")
def observer(server: str):
    """启动 Observer 客户端 - 实时查看 Agent 交互过程"""
    from observers.client import ObserverClient

    console.print(Panel("DevAgent Observer", title="Starting"))
    console.print(f"连接到服务器：{server}")

    client = ObserverClient(server_url=server)

    try:
        asyncio.run(client.connect_and_listen())
    except KeyboardInterrupt:
        console.print("\n[blue]Observer 已断开连接[/blue]")


@cli.command()
@click.option("--port", "-p", default=8765, help="服务器端口")
@click.option("--host", "-h", default="127.0.0.1", help="监听地址")
def observer_server(port: int, host: str):
    """启动 Observer 服务器"""
    from observers.server import ObserverServer

    server = ObserverServer(host=host, port=port)
    console.print(f"[green]启动 Observer 服务器于 {host}:{port}[/green]")
    console.print("[yellow]按 Ctrl+C 停止[/yellow]")

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        console.print("\n[blue]Observer 服务器已停止[/blue]")


@cli.command()
@click.argument("session_id", required=False)
def replay(session_id: str | None):
    """回放历史会话"""
    from observers.logger import JSONLogger

    logger = JSONLogger()

    if not session_id:
        # 列出所有会话
        sessions = logger.list_sessions()
        if not sessions:
            console.print("[yellow]没有找到历史会话[/yellow]")
            return

        console.print("\n[bold]历史会话列表:[/bold]\n")
        for s in sessions[:10]:  # 显示最近 10 个
            start_time = s.get("start_time", "N/A")
            if start_time and start_time != "None":
                start_time = start_time[:19]  # 截取 ISO 格式
            console.print(f"  {s['session_id']} | {start_time} | {s['event_count']} 个事件")
        console.print("\n使用 [bold]dev-agent replay <session_id>[/bold] 回放指定会话")
    else:
        # 回放指定会话
        session = logger.load_session(session_id)
        if not session:
            console.print(f"[red]未找到会话：{session_id}[/red]")
            return

        console.print(Panel(f"回放会话：{session_id}", title="Replay"))
        for event in session.events:
            timestamp = event.timestamp.strftime("%H:%M:%S") if event.timestamp else "??:??:??"
            console.print(f"\n[{event.event_type.value}] {timestamp}")
            console.print(f"  {event.data}")


@cli.command()
@click.option("--port", "-p", default=8765, help="服务器端口")
def watch(port: int):
    """一键启动 Observer - 自动启动服务器和客户端

    这是最简单的 Observer 启动方式，无需手动启动服务器。
    会在后台启动 WebSocket 服务器，然后打开客户端界面。

    使用方法:
    1. 运行此命令启动 Observer
    2. 在另一个终端运行: dev-agent interactive --observe
    3. 或在另一个终端运行: dev-agent run --observe "你的需求"
    """
    import subprocess
    import sys
    import time

    console.print(Panel("一键启动 Observer", title="Starting"))
    console.print("\n[yellow]使用说明:[/yellow]")
    console.print("  1. 本终端已启动 Observer 服务器和客户端")
    console.print("  2. 请打开另一个终端，运行以下命令开始会话:")
    console.print("     [bold]dev-agent interactive --observe[/bold]")
    console.print("     或 [bold]dev-agent run --observe \"你的需求\"[/bold]")
    console.print()

    # 启动后台服务器
    console.print("[dim]正在启动 Observer 服务器...[/dim]")

    # 使用 subprocess 启动后台进程
    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.cli.main", "observer-server", "--port", str(port)],
        creationflags=subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0,
    )

    # 等待服务器启动
    time.sleep(2)  # 增加等待时间

    console.print(f"[green]服务器已启动于 127.0.0.1:{port}[/green]")
    console.print("[green]请在另一个终端运行：dev-agent interactive --observe[/green]")
    console.print("[dim]按 Ctrl+C 停止观察[/dim]\n")

    # 启动客户端
    from observers.client import ObserverClient

    client = ObserverClient(server_url=f"ws://127.0.0.1:{port}")

    try:
        asyncio.run(client.connect_and_listen())
    except KeyboardInterrupt:
        console.print("\n[blue]Observer 已断开连接[/blue]")
    finally:
        server_process.terminate()


if __name__ == "__main__":
    cli()
