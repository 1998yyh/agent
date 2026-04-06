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
