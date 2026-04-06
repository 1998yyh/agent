"""SessionLog 单元测试"""

import pytest
from datetime import datetime
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from observers.session import SessionLog
from observers.events import Event, EventType


def test_session_log_creation():
    """测试 SessionLog 创建"""
    log = SessionLog(session_id="test_123")
    assert log.session_id == "test_123"
    assert log.events == []
    assert log.start_time is None
    assert log.end_time is None
    assert log.metadata == {}


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
    assert log.metadata.get("model") == "glm-5"

    end_event = Event(
        event_type=EventType.SESSION_END,
        session_id="test_123",
        data={"total_tokens": 1000}
    )
    log.add_event(end_event)
    assert log.end_time is not None
    assert log.metadata.get("total_tokens") == 1000


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
    assert d["events"][0]["type"] == "user_message"


def test_session_log_from_dict():
    """测试 SessionLog 从字典反序列化"""
    d = {
        "session_id": "test_456",
        "start_time": "2026-04-06T14:30:00",
        "end_time": "2026-04-06T14:35:00",
        "metadata": {"model": "glm-5"},
        "events": [
            {
                "type": "user_message",
                "session_id": "test_456",
                "timestamp": "2026-04-06T14:30:00Z",
                "data": {"content": "Hello"}
            }
        ]
    }
    log = SessionLog.from_dict(d)
    assert log.session_id == "test_456"
    assert log.start_time is not None
    assert log.metadata["model"] == "glm-5"
    assert len(log.events) == 1


def test_session_log_get_duration():
    """测试获取会话持续时间"""
    log = SessionLog(session_id="test_789")

    # 没有时间时返回 None
    assert log.get_duration() is None

    # 设置开始和结束时间
    log.start_time = datetime(2026, 4, 6, 14, 30, 0)
    log.end_time = datetime(2026, 4, 6, 14, 35, 0)
    assert log.get_duration() == 300.0  # 5 分钟 = 300 秒
