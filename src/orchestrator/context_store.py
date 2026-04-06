"""工作流上下文 - 在各 Agent 之间传递状态"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import uuid


@dataclass
class WorkflowContext:
    """工作流上下文 - 在各 Agent 之间传递状态

    Attributes:
        workflow_id: 工作流唯一标识符
        user_request: 用户原始需求
        current_stage: 当前阶段
        stages_completed: 已完成的阶段列表
        requirements_doc: 需求文档
        design_doc: 技术设计文档
        source_files: 源代码文件列表
        test_results: 测试结果
        delivery_report: 交付报告
        package_path: 打包路径
        created_at: 创建时间
        updated_at: 更新时间
        errors: 错误列表
        current_messages: 临时消息列表（不持久化）
    """

    # 基本信息
    workflow_id: str = field(default_factory=lambda: f"wf_{uuid.uuid4().hex[:8]}")
    user_request: str = ""
    current_stage: str = ""
    stages_completed: list = field(default_factory=list)

    # 各阶段产物
    requirements_doc: Optional[str] = None
    design_doc: Optional[str] = None
    source_files: list[str] = field(default_factory=list)
    test_results: Optional[dict[str, Any]] = None
    delivery_report: Optional[str] = None
    package_path: Optional[str] = None

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 错误信息
    errors: list[str] = field(default_factory=list)

    # 临时变量（不持久化）
    current_messages: list[dict] = field(default_factory=list, repr=False)

    def update(self, **kwargs) -> "WorkflowContext":
        """更新上下文

        Args:
            **kwargs: 要更新的键值对

        Returns:
            更新后的上下文实例
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now().isoformat()
        return self

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（用于持久化）

        Returns:
            字典格式的上下文数据
        """
        return {
            "workflow_id": self.workflow_id,
            "user_request": self.user_request,
            "current_stage": self.current_stage,
            "stages_completed": self.stages_completed,
            "requirements_doc": self.requirements_doc,
            "design_doc": self.design_doc,
            "source_files": self.source_files,
            "test_results": self.test_results,
            "delivery_report": self.delivery_report,
            "package_path": self.package_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowContext":
        """从字典加载上下文

        Args:
            data: 字典格式的上下文数据

        Returns:
            WorkflowContext 实例
        """
        return cls(
            workflow_id=data.get("workflow_id", f"wf_{uuid.uuid4().hex[:8]}"),
            user_request=data.get("user_request", ""),
            current_stage=data.get("current_stage", ""),
            stages_completed=data.get("stages_completed", []),
            requirements_doc=data.get("requirements_doc"),
            design_doc=data.get("design_doc"),
            source_files=data.get("source_files", []),
            test_results=data.get("test_results"),
            delivery_report=data.get("delivery_report"),
            package_path=data.get("package_path"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            errors=data.get("errors", []),
        )


class ContextStore:
    """上下文存储 - 管理状态持久化

    Attributes:
        storage_dir: 存储目录路径
        _cache: 内存缓存字典
    """

    def __init__(self, storage_dir: str = "./storage/workflows"):
        """初始化上下文存储

        Args:
            storage_dir: 存储目录路径
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self._cache: dict[str, WorkflowContext] = {}

    def create(self, user_request: str) -> WorkflowContext:
        """创建新的工作流上下文

        Args:
            user_request: 用户需求描述

        Returns:
            新创建的上下文实例
        """
        context = WorkflowContext(user_request=user_request)
        self._cache[context.workflow_id] = context
        return context

    def get(self, workflow_id: str) -> Optional[WorkflowContext]:
        """获取工作流上下文

        Args:
            workflow_id: 工作流 ID

        Returns:
            上下文实例，不存在则返回 None
        """
        # 先从缓存获取
        if workflow_id in self._cache:
            return self._cache[workflow_id]

        # 从磁盘加载
        return self._load_from_disk(workflow_id)

    async def save(self, context: WorkflowContext) -> None:
        """保存工作流上下文

        Args:
            context: 要保存的上下文实例
        """
        # 更新缓存
        self._cache[context.workflow_id] = context

        # 持久化到磁盘
        self._save_to_disk(context)

    def _save_to_disk(self, context: WorkflowContext) -> None:
        """保存到磁盘

        Args:
            context: 要保存的上下文实例
        """
        filepath = self.storage_dir / f"{context.workflow_id}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(context.to_dict(), f, ensure_ascii=False, indent=2)

    def _load_from_disk(self, workflow_id: str) -> Optional[WorkflowContext]:
        """从磁盘加载上下文

        Args:
            workflow_id: 工作流 ID

        Returns:
            上下文实例，加载失败返回 None
        """
        filepath = self.storage_dir / f"{workflow_id}.json"

        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        context = WorkflowContext.from_dict(data)
        self._cache[workflow_id] = context
        return context

    def list_workflows(self) -> list[dict[str, Any]]:
        """列出所有工作流

        Returns:
            工作流信息列表，按创建时间倒序
        """
        workflows = []
        for filepath in self.storage_dir.glob("*.json"):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                workflows.append({
                    "workflow_id": data["workflow_id"],
                    "user_request": data["user_request"],
                    "created_at": data["created_at"],
                    "stages_completed": data["stages_completed"],
                })
        return sorted(workflows, key=lambda x: x["created_at"], reverse=True)

    def delete(self, workflow_id: str) -> bool:
        """删除工作流上下文

        Args:
            workflow_id: 工作流 ID

        Returns:
            是否删除成功
        """
        # 从缓存删除
        if workflow_id in self._cache:
            del self._cache[workflow_id]

        # 从磁盘删除
        filepath = self.storage_dir / f"{workflow_id}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False
