# Observer 工具设计文档

> 实时查看 Agent 交互过程的观察者工具
>
> 版本：1.0
>
> 创建日期：2026-04-06

---

## 1. 概述

### 1.1 目标

Observer 工具允许用户实时查看 Agent 的完整交互过程，包括：
- 用户提问
- AI 思考过程（think 工具内容）
- 工具调用和结果
- API 调用详情（模型、token 使用）
- AI 最终回答

### 1.2 核心功能

| 功能 | 说明 |
|------|------|
| **实时观察** | 通过 WebSocket 实时接收 Agent 事件 |
| **日志持久化** | 会话保存到 JSON 文件 |
| **历史回放** | 回放历史会话记录 |
| **TUI 界面** | Rich 终端界面，分面板显示各类事件 |

### 1.3 非目标（后续阶段）

- Web 可视化仪表板（阶段 3）
- 多会话对比
- 事件过滤和搜索

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI (主进程)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │    Agent     │→│ ObserverHook │→│  JSON Logger     │  │
│  │  (事件触发)  │  │  (回调分发)  │  │  (存储到文件)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         │                                                   │
│         │ WebSocket                                         │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Observer Server (后台)                  │   │
│  │         - 接收事件                                    │   │
│  │         - 广播给连接的客户端                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ WebSocket
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              Observer CLI (独立进程)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Rich TUI 界面                                       │  │
│  │   - 用户提问面板                                      │  │
│  │   - AI 思考过程面板                                   │  │
│  │   - 工具调用面板                                      │  │
│  │   - API 调用面板                                      │  │
│  │   - 最终回答面板                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 组件职责

| 组件 | 职责 |
|------|------|
| **ObserverHook** | 注入到 Agent 中，捕获各类事件并分发给 Logger 和 Server |
| **ObserverServer** | WebSocket 服务器，接收事件并广播给连接的客户端 |
| **ObserverClient** | CLI 观察者客户端，连接服务器并显示 TUI 界面 |
| **JSONLogger** | 将事件序列化到 JSON 文件 |

---

## 3. 事件类型定义

### 3.1 EventType 枚举

```python
class EventType(Enum):
    SESSION_START = "session_start"    # 会话开始
    USER_MESSAGE = "user_message"      # 用户提问
    AI_THINKING = "ai_thinking"        # AI 思考 (think 工具)
    TOOL_CALL = "tool_call"            # 工具调用开始
    TOOL_RESULT = "tool_result"        # 工具返回结果
    API_CALL = "api_call"              # Claude API 调用
    API_RESPONSE = "api_response"      # API 响应
    AI_RESPONSE = "ai_response"        # AI 最终回答
    SESSION_END = "session_end"        # 会话结束
```

### 3.2 Event 数据结构

```python
@dataclass
class Event:
    type: EventType           # 事件类型
    timestamp: datetime       # 时间戳
    session_id: str           # 会话 ID
    data: dict[str, Any]      # 事件数据
```

### 3.3 各事件类型的数据格式

| 事件类型 | data 字段 |
|----------|----------|
| `session_start` | `{"model": str, "tools": list}` |
| `user_message` | `{"content": str}` |
| `ai_thinking` | `{"content": str}` |
| `tool_call` | `{"name": str, "input": dict, "id": str}` |
| `tool_result` | `{"name": str, "result": str, "id": str}` |
| `api_call` | `{"model": str, "max_tokens": int}` |
| `api_response` | `{"usage": dict, "content": list}` |
| `ai_response` | `{"content": str}` |
| `session_end` | `{"total_tokens": int, "duration": float}` |

---

## 4. 核心组件设计

### 4.1 ObserverHook

**文件**: `src/observers/hook.py`

```python
class ObserverHook:
    """观察者钩子 - 注入到 Agent 中捕获事件"""

    def __init__(
        self,
        session_id: str,
        logger: JSONLogger,
        server_client: WebSocketClient
    ):
        self.session_id = session_id
        self.logger = logger
        self.server_client = server_client

    async def on_user_message(self, content: str):
        """用户提问事件"""
        event = Event(EventType.USER_MESSAGE, self.session_id, {"content": content})
        await self._emit(event)

    async def on_tool_call(self, name: str, input: dict, tool_id: str):
        """工具调用事件"""
        event = Event(EventType.TOOL_CALL, self.session_id, {
            "name": name,
            "input": input,
            "id": tool_id
        })
        await self._emit(event)

    async def on_tool_result(self, name: str, result: str, tool_id: str):
        """工具结果事件"""
        event = Event(EventType.TOOL_RESULT, self.session_id, {
            "name": name,
            "result": result,
            "id": tool_id
        })
        await self._emit(event)

    async def on_api_call(self, model: str, max_tokens: int):
        """API 调用事件"""
        event = Event(EventType.API_CALL, self.session_id, {
            "model": model,
            "max_tokens": max_tokens
        })
        await self._emit(event)

    async def on_ai_thinking(self, content: str):
        """AI 思考事件"""
        event = Event(EventType.AI_THINKING, self.session_id, {"content": content})
        await self._emit(event)

    async def on_ai_response(self, content: str, usage: dict):
        """AI 响应事件"""
        event = Event(EventType.AI_RESPONSE, self.session_id, {
            "content": content,
            "usage": usage
        })
        await self._emit(event)

    async def _emit(self, event: Event):
        """发送事件到 Logger 和 Server"""
        await asyncio.gather(
            self.logger.log(event),
            self.server_client.send(event.to_dict())
        )
```

### 4.2 ObserverServer

**文件**: `src/observers/server.py`

```python
class ObserverServer:
    """WebSocket 服务器 - 广播事件给客户端"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: set[WebSocketClient] = set()

    async def start(self):
        """启动服务器"""
        async with serve(self.handler, self.host, self.port):
            await asyncio.Future()

    async def handler(self, websocket):
        """处理客户端连接"""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                pass  # 只接收，不处理客户端消息
        finally:
            self.clients.remove(websocket)

    async def broadcast(self, event: dict):
        """广播事件给所有客户端"""
        if self.clients:
            await asyncio.gather(
                *[client.send(event) for client in self.clients],
                return_exceptions=True
            )
```

### 4.3 JSONLogger

**文件**: `src/observers/logger.py`

```python
class JSONLogger:
    """JSON 日志记录器"""

    def __init__(self, base_dir: str = "storage/logs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.session: SessionLog | None = None

    def start_session(self, session_id: str) -> str:
        """开始新会话，返回日志文件路径"""
        self.session = SessionLog(session_id=session_id)
        return self.get_log_path(session_id)

    def get_log_path(self, session_id: str) -> Path:
        """获取日志文件路径"""
        return self.base_dir / f"{session_id}.json"

    async def log(self, event: Event):
        """记录事件"""
        if self.session:
            self.session.add_event(event)

    def save(self):
        """保存会话到文件"""
        if self.session:
            path = self.get_log_path(self.session.session_id)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.session.to_dict(), f, indent=2, ensure_ascii=False)
```

### 4.4 ObserverClient (CLI)

**文件**: `src/observers/client.py`

```python
class ObserverClient:
    """观察者客户端 - Rich TUI 界面"""

    def __init__(self, server_url: str = "ws://127.0.0.1:8765"):
        self.server_url = server_url
        self.console = Console()
        self.layout = None
        self.events_buffer = []

    async def connect(self):
        """连接到服务器"""
        async with connect(self.server_url) as websocket:
            async for message in websocket:
                event = Event.from_dict(message)
                self.handle_event(event)

    def handle_event(self, event: Event):
        """处理事件并更新 TUI"""
        self.events_buffer.append(event)

        if event.type == EventType.USER_MESSAGE:
            self.update_user_panel(event.data["content"])
        elif event.type == EventType.AI_THINKING:
            self.update_thinking_panel(event.data["content"])
        elif event.type == EventType.TOOL_CALL:
            self.update_tool_panel(event.data)
        elif event.type == EventType.AI_RESPONSE:
            self.update_response_panel(event.data["content"])

    def render(self):
        """渲染 TUI 界面"""
        # 使用 Rich Layout 分屏显示
        ...
```

---

## 5. CLI 命令设计

### 5.1 命令结构

```bash
# 启动观察者服务器（后台运行）
dev-agent observer-server start

# 查看服务器状态
dev-agent observer-server status

# 停止服务器
dev-agent observer-server stop

# 启动观察者客户端（连接到服务器）
dev-agent observer

# 运行 Agent 并启用观察者钩子
dev-agent run --observe "创建项目"

# 交互模式下启用观察者
dev-agent interactive --observe

# 回放历史日志
dev-agent replay <session_id>

# 列出历史会话
dev-agent replay --list
```

### 5.2 CLI 入口

**文件**: `src/cli/observer_cli.py`

```python
@click.group()
def observer_cli():
    """Observer 工具 - 实时查看 Agent 交互过程"""
    pass

@observer_cli.command()
def start():
    """启动观察者服务器"""
    ...

@observer_cli.command()
def status():
    """查看服务器状态"""
    ...

@observer_cli.command()
def stop():
    """停止服务器"""
    ...

@click.command()
@click.option("--server", "-s", default="ws://127.0.0.1:8765")
def observe(server: str):
    """启动观察者客户端"""
    ...

@click.command()
@click.argument("session_id")
def replay(session_id: str):
    """回放历史会话"""
    ...
```

---

## 6. 目录结构

```
src/
├── observers/                  # Observer 模块
│   ├── __init__.py
│   ├── hook.py                 # ObserverHook - 钩子
│   ├── server.py               # ObserverServer - WebSocket 服务器
│   ├── client.py               # ObserverClient - CLI 客户端
│   ├── logger.py               # JSONLogger - 日志记录器
│   ├── events.py               # Event 和 EventType 定义
│   └── session.py              # SessionLog - 会话日志
│
├── cli/
│   ├── main.py                 # 主 CLI 入口
│   └── observer_cli.py         # Observer CLI 命令
│
storage/
└── logs/                       # 日志文件目录
    └── <session_id>.json
```

---

## 7. 依赖

```txt
# requirements.txt 新增
websockets>=12.0              # WebSocket 支持
aiofiles>=23.0                # 异步文件操作
```

---

## 8. 测试计划

### 8.1 单元测试

| 测试模块 | 测试内容 |
|----------|----------|
| `tests/observers/test_events.py` | Event 序列化/反序列化 |
| `tests/observers/test_hook.py` | ObserverHook 事件捕获 |
| `tests/observers/test_logger.py` | JSONLogger 日志写入 |
| `tests/observers/test_server.py` | WebSocket 服务器广播 |

### 8.2 集成测试

| 测试场景 | 说明 |
|----------|------|
| `test_observer_end_to_end` | 完整事件流：Agent → Hook → Server → Client |
| `test_log_file_format` | 日志文件格式正确 |
| `test_replay_session` | 回放历史会话 |

---

## 9. 实施计划

### 阶段 1：核心事件系统
- [ ] 创建 Event 和 EventType 定义
- [ ] 创建 ObserverHook 钩子类
- [ ] 创建 JSONLogger 日志记录器

### 阶段 2：WebSocket 通信
- [ ] 创建 ObserverServer 服务器
- [ ] 创建 ObserverClient 客户端（基础版）

### 阶段 3：CLI 集成
- [ ] 添加 observer-server 命令
- [ ] 添加 observer 命令
- [ ] 添加 --observe 标志到 run 和 interactive 命令
- [ ] 添加 replay 命令

### 阶段 4：TUI 界面
- [ ] 使用 Rich Layout 创建分屏界面
- [ ] 实现事件驱动的界面更新

### 阶段 5：测试和文档
- [ ] 编写单元测试
- [ ] 编写使用文档

---

## 10. 使用示例

### 启动观察者

```bash
# 终端 1：启动服务器
dev-agent observer-server start

# 终端 2：启动观察者客户端
dev-agent observer

# 终端 3：运行 Agent（带观察者钩子）
dev-agent run --observe "创建一个 Python 计算器项目"
```

### 回放历史

```bash
# 列出历史会话
dev-agent replay --list

# 回放指定会话
dev-agent replay 20260406_143022_abc123
```

---

## 11. 配置选项

```python
@dataclass
class ObserverConfig:
    server_host: str = "127.0.0.1"
    server_port: int = 8765
    log_dir: str = "storage/logs"
    auto_start_server: bool = True  # 自动启动服务器
```

---

## 12. 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| 服务器未启动 | 客户端提示用户先启动服务器 |
| WebSocket 连接失败 | 重试 3 次，失败后显示错误 |
| 日志文件写入失败 | 降级到内存缓冲，恢复后写入 |
| 会话 ID 冲突 | 使用时间戳 + 随机字符串保证唯一性 |

---

## 13. 未来扩展

- [ ] Web 可视化仪表板
- [ ] 事件过滤和搜索
- [ ] 多会话对比视图
- [ ] 导出为 HTML 报告
- [ ] 实时指标统计（token 使用、响应时间）

---

*下一步：实施计划*
