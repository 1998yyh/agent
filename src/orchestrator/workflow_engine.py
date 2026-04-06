"""工作流引擎 - 核心编排逻辑"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .context_store import ContextStore, WorkflowContext
from .checkpoint import CheckpointManager


@dataclass
class StageResult:
    """阶段执行结果

    Attributes:
        success: 是否成功
        output: 输出结果
        error: 错误信息
        can_retry: 是否可重试
    """
    success: bool = True
    output: Any = None
    error: Optional[str] = None
    can_retry: bool = False

    def __post_init__(self):
        if not self.success and not self.error:
            self.error = "未知错误"


class WorkflowEngine:
    """工作流引擎 - 编排多 Agent 协作

    负责管理和调度 5 个专用 Agent 按顺序执行，
    完成从需求分析到交付的完整开发流程。

    Attributes:
        context_store: 上下文存储实例
        checkpoint_manager: 检查点管理器实例
        agents: 注册的 Agent 字典
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
    """

    # 定义工作流阶段
    STAGES = [
        ("requirements", "RequirementsAgent"),
        ("design", "DesignAgent"),
        ("coding", "CodingAgent"),
        ("testing", "TestingAgent"),
        ("delivery", "DeliveryAgent"),
    ]

    def __init__(self):
        """初始化工作流引擎"""
        self.context_store = ContextStore()
        self.checkpoint_manager = CheckpointManager()
        self.agents: dict[str, Callable] = {}
        self._register_agents()

        # 错误处理配置
        self.max_retries = 3
        self.retry_delay = 2.0  # 秒

    def _register_agents(self) -> None:
        """注册所有 Agent"""
        from ..agents_custom.base import RequirementsAgent, DesignAgent, CodingAgent, TestingAgent, DeliveryAgent

        self.agents = {
            "RequirementsAgent": RequirementsAgent,
            "DesignAgent": DesignAgent,
            "CodingAgent": CodingAgent,
            "TestingAgent": TestingAgent,
            "DeliveryAgent": DeliveryAgent,
        }

    async def execute(self, user_request: str) -> dict[str, Any]:
        """执行完整工作流

        Args:
            user_request: 用户需求描述

        Returns:
            交付物字典，包含工作流状态和各阶段产物
        """
        # 创建上下文
        context = self.context_store.create(user_request)

        print(f"\n{'='*60}")
        print(f"开始工作流 {context.workflow_id}")
        print(f"用户需求：{user_request}")
        print(f"{'='*60}\n")

        for stage_name, agent_name in self.STAGES:
            print(f"\n--- 阶段：{stage_name} ---")
            print(f"Agent: {agent_name}")

            try:
                agent = self.agents[agent_name]()
                result = await agent.execute(context)

                # 更新上下文
                context = result.context
                context.current_stage = stage_name
                context.stages_completed.append(stage_name)

                # 保存检查点
                await self.context_store.save(context)
                self.checkpoint_manager.save_checkpoint(
                    workflow_id=context.workflow_id,
                    stage=stage_name,
                    context=context.to_dict(),
                )

                # 检查结果
                if not result.success:
                    print(f"阶段 {stage_name} 失败：{result.error}")
                    await self._handle_error(stage_name, result, context)
                    break

                print(f"阶段 {stage_name} 完成")

            except Exception as e:
                print(f"阶段 {stage_name} 异常：{str(e)}")
                await self._handle_exception(stage_name, e, context)
                break

        print(f"\n{'='*60}")
        print(f"工作流完成：{context.workflow_id}")
        print(f"{'='*60}\n")

        return self._build_delivery(context)

    async def _handle_error(
        self,
        stage: str,
        result: StageResult,
        context: WorkflowContext,
    ) -> None:
        """错误处理

        Args:
            stage: 阶段名称
            result: 阶段执行结果
            context: 工作流上下文
        """
        context.errors.append(f"{stage}: {result.error}")

        if result.can_retry:
            print("尝试重试...")
            # 重试逻辑可以在这里实现

    async def _handle_exception(
        self,
        stage: str,
        error: Exception,
        context: WorkflowContext,
    ) -> None:
        """异常处理

        Args:
            stage: 阶段名称
            error: 异常实例
            context: 工作流上下文
        """
        context.errors.append(f"{stage}: {str(error)}")
        await self.context_store.save(context)

    def _build_delivery(self, context: WorkflowContext) -> dict[str, Any]:
        """构建交付物

        Args:
            context: 工作流上下文

        Returns:
            交付物字典
        """
        return {
            "workflow_id": context.workflow_id,
            "status": "completed" if context.delivery_report else "failed",
            "stages_completed": context.stages_completed,
            "deliverables": {
                "requirements": context.requirements_doc,
                "design": context.design_doc,
                "source_files": context.source_files,
                "test_results": context.test_results,
                "delivery_report": context.delivery_report,
            },
            "errors": context.errors,
        }

    async def resume_from_checkpoint(self, workflow_id: str) -> dict[str, Any]:
        """从检查点恢复执行

        Args:
            workflow_id: 工作流 ID

        Returns:
            交付物字典
        """
        # 获取最新检查点
        checkpoint = self.checkpoint_manager.get_latest_checkpoint(workflow_id)

        if not checkpoint:
            return {"error": "未找到检查点"}

        # 恢复上下文
        context_data = checkpoint["context"]
        context = WorkflowContext.from_dict(context_data)

        # 找到下一个阶段
        last_stage = checkpoint["stage"]
        next_stage_index = None

        for i, (stage_name, _) in enumerate(self.STAGES):
            if stage_name == last_stage:
                next_stage_index = i + 1
                break

        if next_stage_index is None or next_stage_index >= len(self.STAGES):
            return {"error": "工作流已完成，无需恢复"}

        print(f"从检查点恢复：{workflow_id}")
        print(f"上一个完成的阶段：{last_stage}")
        print(f"下一个阶段：{self.STAGES[next_stage_index][0]}")

        # 继续执行剩余阶段
        context.errors = []  # 清除错误

        for stage_name, agent_name in self.STAGES[next_stage_index:]:
            print(f"\n--- 恢复阶段：{stage_name} ---")

            try:
                agent = self.agents[agent_name]()
                result = await agent.execute(context)

                context = result.context
                context.current_stage = stage_name
                context.stages_completed.append(stage_name)

                await self.context_store.save(context)

                if not result.success:
                    await self._handle_error(stage_name, result, context)
                    break

            except Exception as e:
                await self._handle_exception(stage_name, e, context)
                break

        return self._build_delivery(context)

    def list_workflows(self) -> list[dict[str, Any]]:
        """列出所有工作流

        Returns:
            工作流信息列表
        """
        return self.context_store.list_workflows()

    def get_workflow(self, workflow_id: str) -> Optional[dict[str, Any]]:
        """获取工作流详情

        Args:
            workflow_id: 工作流 ID

        Returns:
            工作流详情字典
        """
        context = self.context_store.get(workflow_id)
        if context:
            return context.to_dict()
        return None
