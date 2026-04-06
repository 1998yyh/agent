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
