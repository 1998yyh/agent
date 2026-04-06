"""JSON 日志记录器"""

import json
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
