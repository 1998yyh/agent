# Observer Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建一个实时 Observer 工具，让用户能够查看 Agent 交互的完整过程（用户提问、AI 思考、工具调用、AI 回答），并自动保存日志到 JSON 文件。

**Architecture:** Observer 系统由 4 个核心组件组成：(1) Event 定义模块 - 标准化事件格式，(2) ObserverHook - 注入 Agent 的事件捕获钩子，(3) JSONLogger - 日志持久化到文件，(4) Observer CLI - 独立命令行客户端，通过 WebSocket 连接服务器实时显示 TUI 界面。

**Tech Stack:** Python asyncio, websockets 库用于 WebSocket 通信，Rich 库用于 TUI 界面，click 用于 CLI 命令，pytest 用于测试。

**Prerequisites:** 需要先安装 `websockets>=12.0` 到 requirements.txt

---

### Task 1: 创建 Event 和 EventType 定义

**Files:**
- Create: `src/observers/__init__.py`
- Create: `src/observers/events.py`
- Create: `src/observers/session.py`
- Test: `tests/observers/test_events.py`

- [ ] **Step 1: Write failing tests for Event and EventType**

```python
# tests/observers/test_events.py
import pytest
from datetime import datetime
from src.observers.events import EventType, Event

def test_event_type_values():
    """测试 EventType 枚举包含所有预期值"""
    assert EventType.SESSION_START.value == "session_start"
    assert EventType.USER_MESSAGE.value == "user_message"
    assert EventType.AI_THINKING.value == "ai_thinking"
    assert EventType.TOOL_CALL.value == "tool_call"
    assert EventType.TOOL_RESULT.value == "tool_result"
    assert EventType.API_CALL.value == "api_call"
    assert EventType.API_RESPONSE.value == "api_response"
    assert EventType.AI_RESPONSE.value == "ai_response"
    assert EventType.SESSION_END.value == "session_end"

def test_event_creation():
    """测试 Event 对象创建"""
    event = Event(
        event_type=EventType.USER_MESSAGE,
        session_id="test_123",
        data={"content": "Hello"}
    )
    assert event.event_type == EventType.USER_MESSAGE
    assert event.session_id == "test_123"
    assert event.data == {"content": "Hello"}
    assert isinstance(event.timestamp, datetime)

def test_event_to_dict():
    """测试 Event 序列化为 dict"""
    event = Event(
        event_type=EventType.TOOL_CALL,
        session_id="test_123",
        data={"name": "file_write", "input": {"path": "test.py"}}
    )
    d = event.to_dict()
    assert d["type"] == "tool_call"
    assert d["session_id"] == "test_123"
    assert d["data"]["name"] == "file_write"
    assert "timestamp" in d

def test_event_from_dict():
    """测试 Event 从 dict 反序列化"""
    d = {
        "type": "ai_thinking",
        "session_id": "test_456",
        "timestamp": "2026-04-06T14:30:00Z",
        "data": {"content": "Let me think..."}
    }
    event = Event.from_dict(d)
    assert event.event_type == EventType.AI_THINKING
    assert event.session_id == "test_456"
    assert event.data["content"] == "Let me think..."
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/observers/test_events.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'src.observers'"

- [ ] **Step 3: Create src/observers/__init__.py**

```python
"""Observer 模块 - 实时查看 Agent 交互过程"""

from .events import EventType, Event
from .session import SessionLog

__all__ = ["EventType", "Event", "SessionLog"]
```

- [ ] **Step 4: Create src/observers/events.py**

```python
"""事件类型和 Event 数据类定义"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(Enum):
    """事件类型枚举"""

    SESSION_START = "session_start"    # 会话开始
    USER_MESSAGE = "user_message"      # 用户提问
    AI_THINKING = "ai_thinking"        # AI 思考 (think 工具)
    TOOL_CALL = "tool_call"            # 工具调用开始
    TOOL_RESULT = "tool_result"        # 工具返回结果
    API_CALL = "api_call"              # Claude API 调用
    API_RESPONSE = "api_response"      # API 响应
    AI_RESPONSE = "ai_response"        # AI 最终回答
    SESSION_END = "session_end"        # 会话结束


@dataclass
class Event:
    """事件数据类

    Attributes:
        event_type: 事件类型
        session_id: 会话唯一标识符
        data: 事件数据字典
        timestamp: 事件时间戳 (自动生成)
    """

    event_type: EventType
    session_id: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """将 Event 序列化为字典

        Returns:
            包含事件所有字段的字典，event_type 转为字符串
        """
        return {
            "type": self.event_type.value,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Event":
        """从字典反序列化 Event

        Args:
            d: 包含事件字段的字典

        Returns:
            Event 实例

        Raises:
            ValueError: 当事件类型无效时
        """
        try:
            event_type = EventType(d["type"])
        except ValueError as e:
            raise ValueError(f"无效的事件类型：{d.get('type')}") from e

        timestamp = datetime.fromisoformat(d["timestamp"]) if "timestamp" in d else datetime.utcnow()

        return cls(
            event_type=event_type,
            session_id=d["session_id"],
            data=d["data"],
            timestamp=timestamp,
        )
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/observers/test_events.py::test_event_type_values -v
```
Expected: PASS

- [ ] **Step 6: Create SessionLog class tests**

```python
# tests/observers/test_session.py (add to)
from src.observers.session import SessionLog
from src.observers.events import Event, EventType

def test_session_log_creation():
    """测试 SessionLog 创建"""
    log = SessionLog(session_id="test_123")
    assert log.session_id == "test_123"
    assert log.events == []
    assert log.start_time is None
    assert log.end_time is None

def test_session_log_add_event():
    """测试添加事件到 SessionLog"""
    log = SessionLog(session_id="test_123")
    event = Event(
        event_type=EventType.USER_MESSAGE,
        session_id="test_123",
        data={"content": "Hello"}
    )
    log.add_event(event)
    assert len(log.events) == 1
    assert log.events[0].event_type == EventType.USER_MESSAGE

def test_session_log_auto_timestamps():
    """测试自动设置开始/结束时间"""
    log = SessionLog(session_id="test_123")
    start_event = Event(
        event_type=EventType.SESSION_START,
        session_id="test_123",
        data={"model": "glm-5"}
    )
    log.add_event(start_event)
    assert log.start_time is not None

    end_event = Event(
        event_type=EventType.SESSION_END,
        session_id="test_123",
        data={"total_tokens": 1000}
    )
    log.add_event(end_event)
    assert log.end_time is not None

def test_session_log_to_dict():
    """测试 SessionLog 序列化为字典"""
    log = SessionLog(session_id="test_123")
    log.add_event(Event(
        event_type=EventType.USER_MESSAGE,
        session_id="test_123",
        data={"content": "Hello"}
    ))
    d = log.to_dict()
    assert d["session_id"] == "test_123"
    assert len(d["events"]) == 1
```

- [ ] **Step 7: Create src/observers/session.py**

```python
"""会话日志管理"""

from datetime import datetime
from typing import Any

from .events import Event, EventType


class SessionLog:
    """会话日志 - 管理单个会话的所有事件

    Attributes:
        session_id: 会话唯一标识符
        events: 事件列表
        start_time: 会话开始时间 (从 SESSION_START 事件提取)
        end_time: 会话结束时间 (从 SESSION_END 事件提取)
        metadata: 会话元数据
    """

    def __init__(self, session_id: str):
        """初始化会话日志

        Args:
            session_id: 会话唯一标识符
        """
        self.session_id = session_id
        self.events: list[Event] = []
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.metadata: dict[str, Any] = {}

    def add_event(self, event: Event):
        """添加事件到会话日志

        Args:
            event: 要添加的事件
        """
        self.events.append(event)

        # 自动设置开始/结束时间
        if event.event_type == EventType.SESSION_START:
            self.start_time = event.timestamp
            self.metadata.update(event.data)
        elif event.event_type == EventType.SESSION_END:
            self.end_time = event.timestamp
            self.metadata.update(event.data)

    def to_dict(self) -> dict[str, Any]:
        """将会话日志序列化为字典

        Returns:
            包含会话所有数据的字典，适合保存为 JSON 文件
        """
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "metadata": self.metadata,
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SessionLog":
        """从字典反序列化会话日志

        Args:
            d: 会话日志字典

        Returns:
            SessionLog 实例
        """
        log = cls(session_id=d["session_id"])

        if d.get("start_time"):
            log.start_time = datetime.fromisoformat(d["start_time"])
        if d.get("end_time"):
            log.end_time = datetime.fromisoformat(d["end_time"])
        log.metadata = d.get("metadata", {})

        for event_dict in d.get("events", []):
            event = Event.from_dict(event_dict)
            log.events.append(event)

        return log

    def get_duration(self) -> float | None:
        """获取会话持续时间 (秒)

        Returns:
            持续秒数，如果开始/结束时间不完整则返回 None
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
```

- [ ] **Step 8: Run tests to verify they pass**

```bash
pytest tests/observers/test_events.py -v
```
Expected: All tests PASS

- [ ] **Step 9: Commit**

```bash
git add src/observers/__init__.py src/observers/events.py src/observers/session.py tests/observers/test_events.py
git commit -m "feat(observer): 创建 Event 和 EventType 定义"
```

---

### Task 2: 创建 JSONLogger 日志记录器

**Files:**
- Create: `src/observers/logger.py`
- Test: `tests/observers/test_logger.py`

- [ ] **Step 1: Write failing tests for JSONLogger**

```python
# tests/observers/test_logger.py
import pytest
import json
import os
from pathlib import Path
from src.observers.logger import JSONLogger
from src.observers.events import Event, EventType


@pytest.fixture
def temp_log_dir(tmp_path):
    """创建临时日志目录"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def logger(temp_log_dir):
    """创建 JSONLogger 实例"""
    return JSONLogger(log_dir=str(temp_log_dir))


def test_logger_creates_log_dir(temp_log_dir):
    """测试日志目录自动创建"""
    new_dir = temp_log_dir.parent / "new_logs"
    JSONLogger(log_dir=str(new_dir))
    assert new_dir.exists()


def test_logger_start_session(logger):
    """测试开始新会话"""
    log_path = logger.start_session("test_123")
    assert str(log_path).endswith("test_123.json")


def test_logger_log_event(logger):
    """测试记录事件"""
    logger.start_session("test_123")
    event = Event(
        event_type=EventType.USER_MESSAGE,
        session_id="test_123",
        data={"content": "Hello"}
    )
    import asyncio
    asyncio.run(logger.log(event))
    assert len(logger.session.events) == 1


def test_logger_save_to_file(logger, temp_log_dir):
    """测试保存到文件"""
    logger.start_session("test_123")
    event = Event(
        event_type=EventType.USER_MESSAGE,
        session_id="test_123",
        data={"content": "Hello"}
    )
    import asyncio
    asyncio.run(logger.log(event))
    logger.save()

    log_path = temp_log_dir / "test_123.json"
    assert log_path.exists()

    with open(log_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["session_id"] == "test_123"
    assert len(data["events"]) == 1
    assert data["events"][0]["type"] == "user_message"


def test_logger_get_log_path(logger, temp_log_dir):
    """测试获取日志文件路径"""
    path = logger.get_log_path("my_session")
    assert path == temp_log_dir / "my_session.json"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/observers/test_logger.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'src.observers.logger'"

- [ ] **Step 3: Create src/observers/logger.py**

```python
"""JSON 日志记录器"""

import json
import asyncio
from pathlib import Path
from typing import Any

from .events import Event
from .session import SessionLog


class JSONLogger:
    """JSON 日志记录器 - 将事件持久化到 JSON 文件

    Attributes:
        log_dir: 日志文件存储目录
        session: 当前会话日志
    """

    def __init__(self, log_dir: str = "storage/logs"):
        """初始化 JSONLogger

        Args:
            log_dir: 日志文件存储目录，不存在会自动创建
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session: SessionLog | None = None

    def start_session(self, session_id: str) -> Path:
        """开始新会话

        Args:
            session_id: 会话唯一标识符

        Returns:
            日志文件路径
        """
        self.session = SessionLog(session_id=session_id)
        return self.get_log_path(session_id)

    def get_log_path(self, session_id: str) -> Path:
        """获取日志文件路径

        Args:
            session_id: 会话标识符

        Returns:
            日志文件完整路径
        """
        return self.log_dir / f"{session_id}.json"

    async def log(self, event: Event):
        """记录事件到当前会话

        Args:
            event: 要记录的事件
        """
        if self.session:
            self.session.add_event(event)
        else:
            # 如果没有活跃会话，自动创建新会话
            self.start_session(event.session_id)
            self.session.add_event(event)

    def save(self):
        """保存当前会话到 JSON 文件

        Raises:
            ValueError: 当没有活跃会话时
        """
        if not self.session:
            raise ValueError("没有活跃的会话可保存")

        path = self.get_log_path(self.session.session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.session.to_dict(), f, indent=2, ensure_ascii=False)

    def load_session(self, session_id: str) -> SessionLog | None:
        """加载历史会话

        Args:
            session_id: 会话标识符

        Returns:
            SessionLog 实例，如果文件不存在则返回 None
        """
        path = self.get_log_path(session_id)
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return SessionLog.from_dict(data)

    def list_sessions(self) -> list[dict[str, Any]]:
        """列出所有历史会话

        Returns:
            会话元数据列表，包含 session_id, start_time, end_time
        """
        sessions = []
        for path in self.log_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data["session_id"],
                    "start_time": data.get("start_time"),
                    "end_time": data.get("end_time"),
                    "event_count": len(data.get("events", [])),
                })
            except (json.JSONDecodeError, KeyError):
                continue

        # 按开始时间倒序排列
        sessions.sort(key=lambda x: x["start_time"] or "", reverse=True)
        return sessions
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/observers/test_logger.py -v
```
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/observers/logger.py tests/observers/test_logger.py
git commit -m "feat(observer): 创建 JSONLogger 日志记录器"
```

---

### Task 3: 创建 ObserverHook 钩子类

**Files:**
- Create: `src/observers/hook.py`
- Create: `src/observers/server_client.py` (WebSocket 客户端，用于发送事件到服务器)
- Test: `tests/observers/test_hook.py`

- [ ] **Step 1: Write failing tests for ObserverHook**

```python
# tests/observers/test_hook.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.observers.hook import ObserverHook
from src.observers.events import Event, EventType


@pytest.fixture
def mock_logger():
    """模拟 JSONLogger"""
    logger = MagicMock()
    logger.log = AsyncMock()
    return logger


@pytest.fixture
def mock_server_client():
    """模拟 WebSocket 客户端"""
    client = MagicMock()
    client.send = AsyncMock()
    return client


@pytest.fixture
def hook(mock_logger, mock_server_client):
    """创建 ObserverHook 实例"""
    return ObserverHook(
        session_id="test_123",
        logger=mock_logger,
        server_client=mock_server_client
    )


@pytest.mark.asyncio
async def test_hook_on_user_message(hook, mock_logger, mock_server_client):
    """测试用户提问事件"""
    await hook.on_user_message("Hello, world!")

    # 验证 Logger 被调用
    assert mock_logger.log.called
    event = mock_logger.log.call_args[0][0]
    assert event.event_type == EventType.USER_MESSAGE
    assert event.data["content"] == "Hello, world!"

    # 验证 Server 被调用
    assert mock_server_client.send.called


@pytest.mark.asyncio
async def test_hook_on_tool_call(hook, mock_logger, mock_server_client):
    """测试工具调用事件"""
    await hook.on_tool_call(
        name="file_write",
        input={"path": "test.py", "content": "print('hi')"},
        tool_id="tool_abc"
    )

    event = mock_logger.log.call_args[0][0]
    assert event.event_type == EventType.TOOL_CALL
    assert event.data["name"] == "file_write"
    assert event.data["input"]["path"] == "test.py"


@pytest.mark.asyncio
async def test_hook_on_tool_result(hook, mock_logger, mock_server_client):
    """测试工具结果事件"""
    await hook.on_tool_result(
        name="file_write",
        result="文件已创建",
        tool_id="tool_abc"
    )

    event = mock_logger.log.call_args[0][0]
    assert event.event_type == EventType.TOOL_RESULT
    assert event.data["result"] == "文件已创建"


@pytest.mark.asyncio
async def test_hook_on_ai_thinking(hook, mock_logger, mock_server_client):
    """测试 AI 思考事件"""
    await hook.on_ai_thinking("Let me analyze this...")

    event = mock_logger.log.call_args[0][0]
    assert event.event_type == EventType.AI_THINKING
    assert event.data["content"] == "Let me analyze this..."


@pytest.mark.asyncio
async def test_hook_on_ai_response(hook, mock_logger, mock_server_client):
    """测试 AI 响应事件"""
    await hook.on_ai_response(
        content="项目已创建完成",
        usage={"input_tokens": 100, "output_tokens": 50}
    )

    event = mock_logger.log.call_args[0][0]
    assert event.event_type == EventType.AI_RESPONSE
    assert event.data["content"] == "项目已创建完成"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/observers/test_hook.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'src.observers.hook'"

- [ ] **Step 3: Create src/observers/server_client.py**

```python
"""WebSocket 客户端 - 连接 Observer 服务器"""

import asyncio
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection


class WebSocketClient:
    """WebSocket 客户端 - 发送事件到服务器

    Attributes:
        server_url: WebSocket 服务器 URL
        connection: WebSocket 连接
    """

    def __init__(self, server_url: str = "ws://127.0.0.1:8765"):
        """初始化客户端

        Args:
            server_url: WebSocket 服务器地址
        """
        self.server_url = server_url
        self.connection: ClientConnection | None = None
        self._connected = False

    async def connect(self):
        """连接到服务器"""
        self.connection = await websockets.connect(self.server_url)
        self._connected = True

    async def disconnect(self):
        """断开连接"""
        if self.connection:
            await self.connection.close()
        self._connected = False

    async def send(self, event: dict[str, Any]):
        """发送事件到服务器

        Args:
            event: 事件字典

        Raises:
            ConnectionError: 当未连接时
        """
        if not self._connected:
            await self.connect()

        import json
        await self.connection.send(json.dumps(event, ensure_ascii=False))

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected and self.connection is not None
```

- [ ] **Step 4: Create src/observers/hook.py**

```python
"""ObserverHook - 注入到 Agent 中捕获事件"""

import asyncio
from typing import Any

from .events import Event, EventType
from .logger import JSONLogger
from .server_client import WebSocketClient


class ObserverHook:
    """观察者钩子 - 注入到 Agent 中捕获并转发事件

    该类提供一系列回调方法，在 Agent 执行的关键节点被调用，
    将事件转发到 Logger(持久化) 和 WebSocket Server(实时广播)。

    Attributes:
        session_id: 会话标识符
        logger: JSON 日志记录器
        server_client: WebSocket 客户端
    """

    def __init__(
        self,
        session_id: str,
        logger: JSONLogger,
        server_client: WebSocketClient | None = None,
        server_url: str = "ws://127.0.0.1:8765"
    ):
        """初始化 ObserverHook

        Args:
            session_id: 会话唯一标识符
            logger: JSON 日志记录器
            server_client: 可选的 WebSocket 客户端实例，不提供则自动创建
            server_url: WebSocket 服务器地址 (仅在自动创建客户端时使用)
        """
        self.session_id = session_id
        self.logger = logger
        self.server_client = server_client
        self._server_url = server_url
        self._owns_client = server_client is None

    async def _ensure_client_connected(self):
        """确保 WebSocket 客户端已连接"""
        if self.server_client and not self.server_client.is_connected:
            try:
                await self.server_client.connect()
            except Exception:
                # 连接失败时静默处理，仅使用本地日志
                pass

    async def _emit(self, event: Event):
        """发送事件到 Logger 和 Server

        Args:
            event: 要发送的事件
        """
        # 记录到本地日志 (总是执行)
        await self.logger.log(event)

        # 发送到服务器 (如果可用)
        if self.server_client:
            try:
                await self._ensure_client_connected()
                if self.server_client.is_connected:
                    await self.server_client.send(event.to_dict())
            except Exception:
                # 发送失败时静默处理
                pass

    async def on_session_start(self, model: str, tools: list[str]):
        """会话开始事件

        Args:
            model: 使用的模型名称
            tools: 可用工具列表
        """
        event = Event(
            event_type=EventType.SESSION_START,
            session_id=self.session_id,
            data={"model": model, "tools": tools}
        )
        await self._emit(event)

    async def on_user_message(self, content: str):
        """用户提问事件

        Args:
            content: 用户输入内容
        """
        event = Event(
            event_type=EventType.USER_MESSAGE,
            session_id=self.session_id,
            data={"content": content}
        )
        await self._emit(event)

    async def on_tool_call(self, name: str, input: dict[str, Any], tool_id: str):
        """工具调用事件

        Args:
            name: 工具名称
            input: 工具输入参数
            tool_id: 工具调用唯一标识符
        """
        event = Event(
            event_type=EventType.TOOL_CALL,
            session_id=self.session_id,
            data={"name": name, "input": input, "id": tool_id}
        )
        await self._emit(event)

    async def on_tool_result(self, name: str, result: str, tool_id: str):
        """工具结果事件

        Args:
            name: 工具名称
            result: 工具执行结果
            tool_id: 工具调用唯一标识符
        """
        event = Event(
            event_type=EventType.TOOL_RESULT,
            session_id=self.session_id,
            data={"name": name, "result": result, "id": tool_id}
        )
        await self._emit(event)

    async def on_ai_thinking(self, content: str):
        """AI 思考事件

        Args:
            content: 思考内容
        """
        event = Event(
            event_type=EventType.AI_THINKING,
            session_id=self.session_id,
            data={"content": content}
        )
        await self._emit(event)

    async def on_api_call(self, model: str, max_tokens: int):
        """API 调用事件

        Args:
            model: 使用的模型名称
            max_tokens: 最大 token 数
        """
        event = Event(
            event_type=EventType.API_CALL,
            session_id=self.session_id,
            data={"model": model, "max_tokens": max_tokens}
        )
        await self._emit(event)

    async def on_api_response(self, usage: dict[str, int], content: list):
        """API 响应事件

        Args:
            usage: Token 使用统计
            content: 响应内容
        """
        event = Event(
            event_type=EventType.API_RESPONSE,
            session_id=self.session_id,
            data={"usage": usage, "content": content}
        )
        await self._emit(event)

    async def on_ai_response(self, content: str, usage: dict[str, int]):
        """AI 最终响应事件

        Args:
            content: AI 回答内容
            usage: Token 使用统计
        """
        event = Event(
            event_type=EventType.AI_RESPONSE,
            session_id=self.session_id,
            data={"content": content, "usage": usage}
        )
        await self._emit(event)

    async def on_session_end(self, total_tokens: int, duration: float):
        """会话结束事件

        Args:
            total_tokens: 总 token 使用量
            duration: 会话持续时间 (秒)
        """
        event = Event(
            event_type=EventType.SESSION_END,
            session_id=self.session_id,
            data={"total_tokens": total_tokens, "duration": duration}
        )
        await self._emit(event)
        # 保存日志到文件
        self.logger.save()

    async def close(self):
        """关闭钩子，清理资源"""
        if self._owns_client and self.server_client:
            await self.server_client.disconnect()
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/observers/test_hook.py -v
```
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/observers/hook.py src/observers/server_client.py tests/observers/test_hook.py
git commit -m "feat(observer): 创建 ObserverHook 钩子类"
```

---

### Task 4: 集成 ObserverHook 到 Agent

**Files:**
- Modify: `src/agents/agent.py`
- Modify: `src/cli/main.py`

- [ ] **Step 1: Add ObserverHook import and integration to Agent**

- [ ] **Step 2: Modify Agent.__init__ to accept optional hook**

```python
# src/agents/agent.py - 在 __init__ 方法中添加

def __init__(
    self,
    name: str,
    system: str,
    tools: list[Tool] | None = None,
    mcp_servers: list[dict[str, Any]] | None = None,
    config: ModelConfig | None = None,
    verbose: bool = False,
    client: Anthropic | None = None,
    message_params: dict[str, Any] | None = None,
    observer_hook: Any | None = None,  # 新增：ObserverHook 实例
):
    # ... 现有代码 ...
    self.observer_hook = observer_hook  # 新增
```

- [ ] **Step 3: Modify _agent_loop to call hook methods**

在 `_agent_loop` 方法中，在适当位置添加 hook 调用：

```python
# 在用户输入后
if self.observer_hook:
    await self.observer_hook.on_user_message(user_input)

# 在 API 调用前
if self.observer_hook:
    await self.observer_hook.on_api_call(
        self.config.model,
        self.config.max_tokens
    )

# 在工具调用时
if self.observer_hook:
    for tool_call in tool_calls:
        await self.observer_hook.on_tool_call(
            tool_call.name,
            tool_call.input,
            tool_call.id
        )

# 在工具结果后
if self.observer_hook:
    for block in tool_results:
        await self.observer_hook.on_tool_result(
            block.get("name", ""),
            block.get("content", ""),
            block.get("tool_use_id", "")
        )

# 在 AI 响应时
if self.observer_hook:
    text_content = ""
    for block in response.content:
        if block.type == "text":
            text_content += block.text
    await self.observer_hook.on_ai_response(
        text_content,
        dict(response.usage) if hasattr(response, "usage") else {}
    )
```

- [ ] **Step 4: Modify CLI run command to create hook**

在 `src/cli/main.py` 的 `run` 命令中：

```python
# 在创建 Agent 前添加
@click.option(
    "--observe",
    "-o",
    is_flag=True,
    help="启用 Observer 实时观察",
)
def run(request: str, workflow_id: str, verbose: bool, model: str, base_url: str, observe: bool):
    # ... 现有代码 ...

    if observe:
        from src.observers.hook import ObserverHook
        from src.observers.logger import JSONLogger
        from src.observers.server_client import WebSocketClient
        import uuid

        session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        logger = JSONLogger()
        logger.start_session(session_id)
        client = WebSocketClient()
        hook = ObserverHook(session_id=session_id, logger=logger, server_client=client)
    else:
        hook = None

    agent = Agent(
        # ... 现有参数 ...
        observer_hook=hook,
    )
```

- [ ] **Step 5: Run tests to verify Agent integration**

```bash
pytest tests/agents/test_agent.py -v
```
Expected: All tests PASS (existing tests should still pass)

- [ ] **Step 6: Commit**

```bash
git add src/agents/agent.py src/cli/main.py
git commit -m "feat(observer): 集成 ObserverHook 到 Agent"
```

---

### Task 5: 创建 ObserverServer WebSocket 服务器

**Files:**
- Create: `src/observers/server.py`
- Test: `tests/observers/test_server.py`

- [ ] **Step 1: Write failing tests for ObserverServer**

```python
# tests/observers/test_server.py
import pytest
import asyncio
from src.observers.server import ObserverServer


@pytest.mark.asyncio
async def test_server_start_and_stop():
    """测试服务器启动和停止"""
    server = ObserverServer(port=8766)  # 使用不同端口避免冲突
    task = asyncio.create_task(server.start())
    await asyncio.sleep(0.5)  # 等待服务器启动
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_server_broadcast():
    """测试服务器广播"""
    server = ObserverServer(port=8767)
    # 模拟客户端连接和广播
    # 详细测试需要 mock WebSocket 连接
```

- [ ] **Step 2: Create src/observers/server.py**

```python
"""Observer WebSocket 服务器"""

import asyncio
import json
import logging
from typing import Any

import websockets
from websockets.asyncio.server import ServerConnection, serve

logger = logging.getLogger(__name__)


class ObserverServer:
    """WebSocket 服务器 - 广播事件给所有连接的客户端

    Attributes:
        host: 服务器监听地址
        port: 服务器端口
        clients: 已连接的客户端集合
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        """初始化服务器

        Args:
            host: 监听地址
            port: 监听端口
        """
        self.host = host
        self.port = port
        self.clients: set[ServerConnection] = set()
        self._server = None
        self._serve_task: asyncio.Task | None = None

    async def start(self):
        """启动服务器"""
        logger.info(f"Starting Observer Server on {self.host}:{self.port}")
        async with serve(self._handler, self.host, self.port):
            # 保持服务器运行
            await asyncio.Future()

    async def start_background(self):
        """在后台启动服务器

        Returns:
            asyncio.Task 服务器任务
        """
        self._serve_task = asyncio.create_task(self.start())
        await asyncio.sleep(0.5)  # 等待服务器启动
        return self._serve_task

    async def stop(self):
        """停止服务器"""
        # 关闭所有客户端连接
        for client in list(self.clients):
            await client.close()
        self.clients.clear()

        # 取消服务任务
        if self._serve_task:
            self._serve_task.cancel()
            try:
                await self._serve_task
            except asyncio.CancelledError:
                pass

    async def _handler(self, websocket: ServerConnection):
        """处理客户端连接

        Args:
            websocket: WebSocket 连接
        """
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")

        try:
            # 保持连接，接收但不处理客户端消息
            async for message in websocket:
                pass
        except websockets.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def broadcast(self, event: dict[str, Any]):
        """广播事件给所有客户端

        Args:
            event: 事件字典
        """
        if not self.clients:
            return

        message = json.dumps(event, ensure_ascii=False)
        # 异步发送给所有客户端，忽略失败的发送
        await asyncio.gather(
            *[client.send(message) for client in self.clients],
            return_exceptions=True
        )

    @property
    def client_count(self) -> int:
        """获取已连接客户端数量"""
        return len(self.clients)
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/observers/test_server.py -v
```
Expected: Tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/observers/server.py tests/observers/test_server.py
git commit -m "feat(observer): 创建 ObserverServer WebSocket 服务器"
```

---

### Task 6: 创建 ObserverClient CLI (Rich TUI)

**Files:**
- Create: `src/observers/client.py`
- Modify: `src/cli/main.py` (添加 observer 命令)

- [ ] **Step 1: Create ObserverClient with Rich TUI**

```python
# src/observers/client.py
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
        self.user_panel = None
        self.thinking_panel = None
        self.tool_panel = None
        self.response_panel = None
        self.status_panel = None

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

    async def connect_and_listen(self):
        """连接服务器并监听事件"""
        try:
            async with websockets.connect(self.server_url) as websocket:
                self.console.print("[green]已连接到 Observer 服务器[/green]")
                async for message in websocket:
                    event = json.loads(message)
                    self.handle_event(event)
                    self.console.print()
        except ConnectionRefusedError:
            self.console.print("[red]无法连接到 Observer 服务器，请确保服务器已启动[/red]")
        except Exception as e:
            self.console.print(f"[red]错误：{e}[/red]")

    def handle_event(self, event: dict):
        """处理事件并更新界面"""
        event_type = event.get("type", "")
        data = event.get("data", {})

        if event_type == "session_start":
            self.session_id = event.get("session_id", "")
            self.layout = self.create_layout()
            self.update_header()
            self.console.print(Panel(f"会话开始 | 模型：{data.get('model', 'N/A')}", title="Session"))

        elif event_type == "user_message":
            self.update_user_panel(data.get("content", ""))

        elif event_type == "ai_thinking":
            self.update_thinking_panel(data.get("content", ""))

        elif event_type == "tool_call":
            # 工具调用开始
            pass

        elif event_type == "tool_result":
            self.update_tool_panel(
                data.get("name", ""),
                data.get("result", "")
            )

        elif event_type == "ai_response":
            self.update_response_panel(data.get("content", ""))

        elif event_type == "session_end":
            duration = data.get("duration", 0)
            tokens = data.get("total_tokens", 0)
            self.console.print(Panel(f"会话结束 | 时长：{duration:.1f}s | Tokens: {tokens}", title="Session"))

        # 渲染布局
        if self.layout:
            self.update_header()
            self.console.print(self.layout)
```

- [ ] **Step 2: Add CLI commands to main.py**

```python
# src/cli/main.py - 添加新命令

@cli.command()
@click.option("--server", "-s", default="ws://127.0.0.1:8765", help="Observer 服务器地址")
def observer(server: str):
    """启动 Observer 客户端 - 实时查看 Agent 交互过程"""
    from src.observers.client import ObserverClient

    console.print(Panel("DevAgent Observer", title="Starting"))
    console.print(f"连接到服务器：{server}")

    client = ObserverClient(server_url=server)
    client.layout = client.create_layout()

    try:
        asyncio.run(client.connect_and_listen())
    except KeyboardInterrupt:
        console.print("\n[blue]Observer 已断开连接[/blue]")


@cli.command()
@click.option("--port", "-p", default=8765, help="服务器端口")
@click.option("--host", "-h", default="127.0.0.1", help="监听地址")
def observer_server(port: int, host: str):
    """启动 Observer 服务器"""
    from src.observers.server import ObserverServer

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
    from src.observers.logger import JSONLogger

    logger = JSONLogger()

    if not session_id:
        # 列出所有会话
        sessions = logger.list_sessions()
        if not sessions:
            console.print("[yellow]没有找到历史会话[/yellow]")
            return

        console.print("\n[bold]历史会话列表:[/bold]\n")
        for s in sessions[:10]:  # 显示最近 10 个
            console.print(f"  {s['session_id']} | {s['start_time']} | {s['event_count']} 个事件")
        console.print("\n使用 `dev-agent replay <session_id>` 回放指定会话")
    else:
        # 回放指定会话
        session = logger.load_session(session_id)
        if not session:
            console.print(f"[red]未找到会话：{session_id}[/red]")
            return

        console.print(Panel(f"回放会话：{session_id}", title="Replay"))
        for event in session.events:
            console.print(f"\n[{event.event_type.value}] {event.timestamp}")
            console.print(f"  {event.data}")
```

- [ ] **Step 3: Test CLI commands manually**

```bash
# 测试 Observer 服务器启动
dev-agent observer-server

# 测试 Observer 客户端 (新终端)
dev-agent observer

# 测试 replay 命令
dev-agent replay --list
```

- [ ] **Step 4: Commit**

```bash
git add src/observers/client.py src/cli/main.py
git commit -m "feat(observer): 创建 ObserverClient CLI 和 TUI 界面"
```

---

### Task 7: 更新 requirements.txt 和添加文档

**Files:**
- Modify: `requirements.txt`
- Create: `docs/OBSERVER_USAGE.md`

- [ ] **Step 1: Add websockets dependency**

```txt
# requirements.txt - 添加
websockets>=12.0              # WebSocket 支持
```

- [ ] **Step 2: Create usage documentation**

```markdown
# Observer 工具使用指南

## 快速开始

### 启动 Observer 服务器

```bash
# 后台启动服务器
dev-agent observer-server &

# 或在前台启动
dev-agent observer-server
```

### 启动 Observer 客户端

```bash
# 连接到本地服务器
dev-agent observer

# 连接到远程服务器
dev-agent observer --server ws://192.168.1.100:8765
```

### 运行带观察的 Agent

```bash
# 交互模式
dev-agent interactive --observe

# 单次运行
dev-agent run --observe "创建一个 Python 项目"
```

## 功能说明

### TUI 界面布局

- **左上**: 用户提问
- **左中**: AI 思考过程
- **左下**: AI 最终回答
- **右侧**: 工具调用详情

### 日志文件

日志保存在 `storage/logs/<session_id>.json`

### 回放历史会话

```bash
# 列出所有会话
dev-agent replay

# 回放指定会话
dev-agent replay 20260406_143022_abc123
```
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt docs/OBSERVER_USAGE.md
git commit -m "docs(observer): 添加使用文档和 websockets 依赖"
```

---

## Self-Review Checklist

**1. Spec coverage:** 检查每个设计文档中的功能是否都有对应任务实现
- Event/EventType 定义 ✓ (Task 1)
- ObserverHook ✓ (Task 3)
- JSONLogger ✓ (Task 2)
- ObserverServer ✓ (Task 5)
- ObserverClient TUI ✓ (Task 6)
- CLI 命令集成 ✓ (Task 4, 6)

**2. Placeholder scan:** 没有 TBD/TODO

**3. Type consistency:** 所有方法签名和类型在各任务间保持一致

---

Plan complete and saved to `docs/superpowers/plans/2026-04-06-observer-tool.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
