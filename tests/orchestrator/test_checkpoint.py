"""测试编排层模块"""

import pytest
import asyncio
import json
from pathlib import Path
import tempfile
import shutil

from orchestrator.context_store import WorkflowContext, ContextStore
from orchestrator.checkpoint import CheckpointManager


class TestWorkflowContext:
    """测试工作流上下文"""

    def test_context_creation(self):
        """测试上下文创建"""
        context = WorkflowContext(user_request="测试需求")

        assert context.user_request == "测试需求"
        assert context.workflow_id.startswith("wf_")
        assert context.stages_completed == []
        assert context.errors == []

    def test_context_update(self):
        """测试上下文更新"""
        context = WorkflowContext(user_request="初始需求")

        context.update(requirements_doc="# 需求文档")

        assert context.requirements_doc == "# 需求文档"
        assert context.updated_at is not None

    def test_context_to_dict(self):
        """测试转换为字典"""
        context = WorkflowContext(
            user_request="测试需求",
            requirements_doc="# 需求文档",
        )

        data = context.to_dict()

        assert data["user_request"] == "测试需求"
        assert data["requirements_doc"] == "# 需求文档"
        assert data["workflow_id"] == context.workflow_id

    def test_context_from_dict(self):
        """测试从字典加载"""
        data = {
            "workflow_id": "wf_test123",
            "user_request": "测试需求",
            "current_stage": "requirements",
            "stages_completed": ["requirements"],
            "requirements_doc": "# 需求文档",
            "errors": [],
        }

        context = WorkflowContext.from_dict(data)

        assert context.workflow_id == "wf_test123"
        assert context.user_request == "测试需求"
        assert context.current_stage == "requirements"


class TestContextStore:
    """测试上下文存储"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        dirpath = tempfile.mkdtemp()
        yield dirpath
        shutil.rmtree(dirpath)

    def test_context_store_create(self, temp_dir):
        """测试创建上下文"""
        store = ContextStore(storage_dir=temp_dir)

        context = store.create("测试需求")

        assert context.user_request == "测试需求"
        assert context.workflow_id in store._cache

    def test_context_store_save_and_get(self, temp_dir):
        """测试保存和获取"""
        store = ContextStore(storage_dir=temp_dir)

        context = store.create("测试需求")
        context.requirements_doc = "# 需求文档"

        asyncio.run(store.save(context))

        # 从缓存获取
        cached = store.get(context.workflow_id)
        assert cached is not None
        assert cached.requirements_doc == "# 需求文档"

    def test_context_store_list_workflows(self, temp_dir):
        """测试列出工作流"""
        store = ContextStore(storage_dir=temp_dir)

        # 创建两个工作流
        ctx1 = store.create("需求 1")
        ctx2 = store.create("需求 2")

        asyncio.run(store.save(ctx1))
        asyncio.run(store.save(ctx2))

        workflows = store.list_workflows()

        assert len(workflows) == 2
        # 按创建时间倒序
        assert workflows[0]["created_at"] >= workflows[1]["created_at"]

    def test_context_store_delete(self, temp_dir):
        """测试删除工作流"""
        store = ContextStore(storage_dir=temp_dir)

        context = store.create("测试需求")
        asyncio.run(store.save(context))

        # 删除
        result = store.delete(context.workflow_id)

        assert result is True
        assert context.workflow_id not in store._cache


class TestCheckpointManager:
    """测试检查点管理器"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        dirpath = tempfile.mkdtemp()
        yield dirpath
        shutil.rmtree(dirpath)

    def test_save_checkpoint(self, temp_dir):
        """测试保存检查点"""
        manager = CheckpointManager(checkpoint_dir=temp_dir)

        context = {
            "workflow_id": "wf_test123",
            "user_request": "测试需求",
            "current_stage": "requirements",
        }

        filepath = manager.save_checkpoint(
            workflow_id="wf_test123",
            stage="requirements",
            context=context,
        )

        assert filepath.exists()
        assert "wf_test123_requirements" in filepath.name

    def test_get_latest_checkpoint(self, temp_dir):
        """测试获取最新检查点"""
        manager = CheckpointManager(checkpoint_dir=temp_dir)

        context = {"workflow_id": "wf_test123", "stage": "requirements"}
        manager.save_checkpoint("wf_test123", "requirements", context)

        import time
        time.sleep(1.1)  # 确保时间戳不同（至少 1 秒）

        context2 = {"workflow_id": "wf_test123", "stage": "design"}
        manager.save_checkpoint("wf_test123", "design", context2)

        latest = manager.get_latest_checkpoint("wf_test123")

        assert latest is not None
        assert latest["stage"] == "design"

    def test_get_checkpoint_at_stage(self, temp_dir):
        """测试获取指定阶段的检查点"""
        manager = CheckpointManager(checkpoint_dir=temp_dir)

        context = {"workflow_id": "wf_test123", "stage": "requirements"}
        manager.save_checkpoint("wf_test123", "requirements", context)

        checkpoint = manager.get_checkpoint_at_stage("wf_test123", "requirements")

        assert checkpoint is not None
        assert checkpoint["stage"] == "requirements"

    def test_list_checkpoints(self, temp_dir):
        """测试列出检查点"""
        manager = CheckpointManager(checkpoint_dir=temp_dir)

        context = {"workflow_id": "wf_test123"}
        manager.save_checkpoint("wf_test123", "requirements", context)
        manager.save_checkpoint("wf_test123", "design", context)

        checkpoints = manager.list_checkpoints("wf_test123")

        assert len(checkpoints) == 2
        # 按时间倒序
        assert checkpoints[0]["timestamp"] >= checkpoints[1]["timestamp"]

    def test_delete_checkpoint(self, temp_dir):
        """测试删除检查点"""
        manager = CheckpointManager(checkpoint_dir=temp_dir)

        context = {"workflow_id": "wf_test123"}
        manager.save_checkpoint("wf_test123", "requirements", context)
        manager.save_checkpoint("wf_test123", "design", context)

        # 删除所有
        count = manager.delete_checkpoint("wf_test123")

        assert count == 2

        # 删除指定阶段
        manager.save_checkpoint("wf_test123", "requirements", context)
        count = manager.delete_checkpoint("wf_test123", "requirements")

        assert count == 1
