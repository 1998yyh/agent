"""JSONLogger 单元测试"""

import pytest
import json
from pathlib import Path
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from observers.logger import JSONLogger
from observers.events import Event, EventType


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


def test_logger_load_session(logger, temp_log_dir):
    """测试加载历史会话"""
    logger.start_session("test_123")
    event = Event(
        event_type=EventType.USER_MESSAGE,
        session_id="test_123",
        data={"content": "Hello"}
    )
    import asyncio
    asyncio.run(logger.log(event))
    logger.save()

    loaded = logger.load_session("test_123")
    assert loaded is not None
    assert loaded.session_id == "test_123"
    assert len(loaded.events) == 1


def test_logger_load_nonexistent_session(logger):
    """测试加载不存在的会话"""
    loaded = logger.load_session("nonexistent")
    assert loaded is None


def test_logger_list_sessions(logger, temp_log_dir):
    """测试列出所有会话"""
    # 创建两个会话
    logger.start_session("session_001")
    logger.save()

    logger.start_session("session_002")
    logger.save()

    sessions = logger.list_sessions()
    assert len(sessions) == 2
    session_ids = [s["session_id"] for s in sessions]
    assert "session_001" in session_ids
    assert "session_002" in session_ids


def test_logger_save_without_session(logger):
    """测试保存没有活跃会话时抛出异常"""
    with pytest.raises(ValueError, match="没有活跃的会话可保存"):
        logger.save()
