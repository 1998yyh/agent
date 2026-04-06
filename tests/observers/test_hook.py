"""ObserverHook 钩子类单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from observers.hook import ObserverHook
from observers.events import Event, EventType
from observers.logger import JSONLogger


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
    client.is_connected = True
    client.connect = AsyncMock()
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
    assert event.data["usage"]["input_tokens"] == 100


@pytest.mark.asyncio
async def test_hook_on_session_start(hook, mock_logger, mock_server_client):
    """测试会话开始事件"""
    await hook.on_session_start(model="glm-5", tools=["think", "file_read"])

    event = mock_logger.log.call_args[0][0]
    assert event.event_type == EventType.SESSION_START
    assert event.data["model"] == "glm-5"
    assert event.data["tools"] == ["think", "file_read"]


@pytest.mark.asyncio
async def test_hook_on_session_end(hook, mock_logger, mock_server_client):
    """测试会话结束事件"""
    await hook.on_session_end(total_tokens=1500, duration=300.0)

    event = mock_logger.log.call_args[0][0]
    assert event.event_type == EventType.SESSION_END
    assert event.data["total_tokens"] == 1500
    assert event.data["duration"] == 300.0


@pytest.mark.asyncio
async def test_hook_on_api_call(hook, mock_logger, mock_server_client):
    """测试 API 调用事件"""
    await hook.on_api_call(model="glm-5", max_tokens=4096)

    event = mock_logger.log.call_args[0][0]
    assert event.event_type == EventType.API_CALL
    assert event.data["model"] == "glm-5"
    assert event.data["max_tokens"] == 4096


@pytest.mark.asyncio
async def test_hook_on_api_response(hook, mock_logger, mock_server_client):
    """测试 API 响应事件"""
    await hook.on_api_response(
        usage={"input_tokens": 100, "output_tokens": 50},
        content=[{"type": "text", "text": "Hello"}]
    )

    event = mock_logger.log.call_args[0][0]
    assert event.event_type == EventType.API_RESPONSE
    assert event.data["usage"]["input_tokens"] == 100
