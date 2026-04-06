"""Observer 客户端 - Rich TUI 界面"""

import asyncio
import json
from datetime import datetime

import websockets
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text


class ObserverClient:
    """观察者客户端 - 显示实时事件流"""

    def __init__(self, server_url: str = "ws://127.0.0.1:8765"):
        """初始化客户端

        Args:
            server_url: WebSocket 服务器地址
        """
        self.server_url = server_url
        self.console = Console()
        self.layout = None
        self.session_id = ""
        self.event_log = []
        self._running = True

    def create_layout(self) -> Layout:
        """创建 TUI 布局"""
        layout = Layout()

        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=3),
        )

        layout["left"].split(
            Layout(name="user", size=6),
            Layout(name="thinking"),
            Layout(name="response"),
        )

        layout["right"].update(
            Panel("等待事件...", title="事件日志", border_style="blue")
        )

        layout["header"].update(
            Panel("[bold]DevAgent Observer[/bold]", style="bold white on blue")
        )

        layout["footer"].update(
            Panel("按 Ctrl+C 断开连接", style="dim", justify="center")
        )

        return layout

    def update_header(self):
        """更新头部"""
        self.layout["header"].update(
            Panel(
                f"[bold]DevAgent Observer[/bold] | Session: {self.session_id or 'N/A'}",
                style="bold white on blue"
            )
        )

    def update_user_panel(self, content: str):
        """更新用户提问面板"""
        self.layout["user"].update(
            Panel(
                Text(content, style="green"),
                title="[bold green]用户提问[/bold green]",
                border_style="green"
            )
        )

    def update_thinking_panel(self, content: str):
        """更新 AI 思考面板"""
        self.layout["thinking"].update(
            Panel(
                Text(content, style="yellow"),
                title="[bold yellow]AI 思考[/bold yellow]",
                border_style="yellow"
            )
        )

    def update_tool_panel(self, name: str, result: str):
        """更新工具调用面板"""
        self.layout["right"].update(
            Panel(
                f"[bold cyan]工具：{name}[/bold cyan]\n{result}",
                title="[bold cyan]工具调用[/bold cyan]",
                border_style="cyan"
            )
        )

    def update_response_panel(self, content: str):
        """更新 AI 回答面板"""
        self.layout["response"].update(
            Panel(
                Text(content, style="white"),
                title="[bold white]AI 回答[/bold white]",
                border_style="white"
            )
        )

    def add_event_to_log(self, event_type: str, timestamp: str):
        """添加事件到日志"""
        self.event_log.append(f"[{timestamp}] {event_type}")
        # 只保留最近 20 个事件
        if len(self.event_log) > 20:
            self.event_log = self.event_log[-20:]

        log_text = "\n".join(self.event_log)
        self.layout["right"].update(
            Panel(log_text, title="[bold blue]事件日志[/bold blue]", border_style="blue")
        )

    async def connect_and_listen(self):
        """连接服务器并监听事件"""
        try:
            async with websockets.connect(self.server_url) as websocket:
                self.console.print("[green]已连接到 Observer 服务器[/green]")
                self.layout = self.create_layout()
                self.console.print(self.layout)

                async for message in websocket:
                    event = json.loads(message)
                    self.handle_event(event)
                    self.console.print(self.layout)

        except ConnectionRefusedError:
            self.console.print("[red]无法连接到 Observer 服务器，请确保服务器已启动[/red]")
            self.console.print(f"[yellow]运行以下命令启动服务器：[/yellow]")
            self.console.print("  dev-agent observer-server")
        except websockets.InvalidStatusCode as e:
            self.console.print(f"[red]连接失败：{e}[/red]")
        except Exception as e:
            if self._running:
                self.console.print(f"[red]错误：{e}[/red]")
        finally:
            self._running = False

    def handle_event(self, event: dict):
        """处理事件并更新界面"""
        event_type = event.get("type", "")
        data = event.get("data", {})
        timestamp = event.get("timestamp", "")[:19]  # 截取 ISO 格式时间戳

        if event_type == "session_start":
            self.session_id = event.get("session_id", "")
            self.update_header()
            model = data.get("model", "N/A")
            self.console.print(Panel(f"会话开始 | 模型：{model}", title="Session"))

        elif event_type == "user_message":
            self.update_user_panel(data.get("content", ""))
            self.add_event_to_log("USER_MESSAGE", timestamp)

        elif event_type == "ai_thinking":
            self.update_thinking_panel(data.get("content", ""))
            self.add_event_to_log("AI_THINKING", timestamp)

        elif event_type == "tool_call":
            name = data.get("name", "")
            self.add_event_to_log(f"TOOL_CALL: {name}", timestamp)

        elif event_type == "tool_result":
            self.update_tool_panel(
                data.get("name", ""),
                data.get("result", "")
            )
            self.add_event_to_log("TOOL_RESULT", timestamp)

        elif event_type == "ai_response":
            self.update_response_panel(data.get("content", ""))
            self.add_event_to_log("AI_RESPONSE", timestamp)

        elif event_type == "session_end":
            duration = data.get("duration", 0)
            tokens = data.get("total_tokens", 0)
            self.console.print(Panel(
                f"会话结束 | 时长：{duration:.1f}s | Tokens: {tokens}",
                title="Session"
            ))
            self.add_event_to_log("SESSION_END", timestamp)

        # 更新头部显示会话 ID
        if self.session_id:
            self.update_header()
