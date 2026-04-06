"""Event 和 EventType 单元测试"""

import pytest
from datetime import datetime
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from observers.events import EventType, Event


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
