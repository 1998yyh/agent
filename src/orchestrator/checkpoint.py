"""检查点管理 - 支持断点续跑"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class CheckpointManager:
    """检查点管理器

    用于保存和恢复工作流执行过程中的状态，
    支持断点续跑功能。

    Attributes:
        checkpoint_dir: 检查点存储目录
    """

    def __init__(self, checkpoint_dir: str = "./storage/checkpoints"):
        """初始化检查点管理器

        Args:
            checkpoint_dir: 检查点存储目录
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        workflow_id: str,
        stage: str,
        context: dict[str, Any],
        metadata: Optional[dict[str, Any]] = None,
    ) -> Path:
        """保存检查点

        Args:
            workflow_id: 工作流 ID
            stage: 当前阶段名称
            context: 上下文数据
            metadata: 额外元数据

        Returns:
            检查点文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{workflow_id}_{stage}_{timestamp}.json"
        filepath = self.checkpoint_dir / filename

        checkpoint = {
            "workflow_id": workflow_id,
            "stage": stage,
            "timestamp": timestamp,
            "context": context,
            "metadata": metadata or {},
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)

        return filepath

    def get_latest_checkpoint(self, workflow_id: str) -> Optional[dict[str, Any]]:
        """获取最新检查点

        Args:
            workflow_id: 工作流 ID

        Returns:
            检查点数据，不存在则返回 None
        """
        checkpoints = list(self.checkpoint_dir.glob(f"{workflow_id}_*.json"))

        if not checkpoints:
            return None

        # 按文件修改时间排序，返回最新的
        checkpoints.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest = checkpoints[0]

        with open(latest, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_checkpoint_at_stage(
        self,
        workflow_id: str,
        stage: str,
    ) -> Optional[dict[str, Any]]:
        """获取指定阶段的检查点

        Args:
            workflow_id: 工作流 ID
            stage: 阶段名称

        Returns:
            检查点数据，不存在则返回 None
        """
        checkpoints = list(self.checkpoint_dir.glob(f"{workflow_id}_{stage}_*.json"))

        if not checkpoints:
            return None

        checkpoints.sort(key=lambda x: x.name, reverse=True)

        with open(checkpoints[0], "r", encoding="utf-8") as f:
            return json.load(f)

    def restore_from_checkpoint(self, checkpoint: dict[str, Any]) -> dict[str, Any]:
        """从检查点恢复上下文

        Args:
            checkpoint: 检查点数据

        Returns:
            恢复的上下文数据
        """
        return checkpoint.get("context", {})

    def list_checkpoints(self, workflow_id: str) -> list[dict[str, Any]]:
        """列出工作流的所有检查点

        Args:
            workflow_id: 工作流 ID

        Returns:
            检查点信息列表，按时间倒序
        """
        checkpoints = []
        for filepath in self.checkpoint_dir.glob(f"{workflow_id}_*.json"):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                checkpoints.append({
                    "filepath": str(filepath),
                    "stage": data["stage"],
                    "timestamp": data["timestamp"],
                })
        return sorted(checkpoints, key=lambda x: x["timestamp"], reverse=True)

    def delete_checkpoint(self, workflow_id: str, stage: Optional[str] = None) -> int:
        """删除检查点

        Args:
            workflow_id: 工作流 ID
            stage: 可选的阶段名称，不指定则删除所有

        Returns:
            删除的检查点数量
        """
        pattern = f"{workflow_id}_{stage}_*.json" if stage else f"{workflow_id}_*.json"
        checkpoints = list(self.checkpoint_dir.glob(pattern))

        deleted_count = 0
        for checkpoint in checkpoints:
            checkpoint.unlink()
            deleted_count += 1

        return deleted_count
