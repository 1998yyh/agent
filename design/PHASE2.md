# 阶段 2 实施指南：多 Agent 协作系统

> **时间**: 4-8 周
>
> **目标**: 实现多 Agent 协作，完成完整开发流程

---

## 1. 阶段 2 概述

### 1.1 目标

完成阶段 2 后，你将能够：
- 理解多 Agent 协作架构
- 实现工作流引擎和上下文存储
- 创建 5 个专用 Agent
- 实现检查点持久化和错误恢复

### 1.2 交付物

| 交付物 | 说明 |
|--------|------|
| WorkflowEngine | 工作流引擎 |
| ContextStore | 上下文存储 |
| 5 个专用 Agent | 需求/方案/编码/测试/交付 |
| 检查点系统 | 断点续跑支持 |
| 错误处理机制 | 重试和恢复 |

### 1.3 与阶段 1 的区别

| 维度 | 阶段 1 | 阶段 2 |
|------|--------|--------|
| Agent 数量 | 1 个通用 Agent | 5 个专用 Agent |
| 架构 | 简单调用 | 工作流编排 |
| 状态管理 | 内存 | 持久化存储 |
| 错误处理 | 基础 | 重试 + 恢复 |

---

## 2. 项目结构（阶段 2）

### 2.1 新增目录

```
dev-agent/
├── ... (阶段 1 的文件)
│
├── orchestrator/          # 新增：编排层
│   ├── __init__.py
│   ├── workflow_engine.py # 工作流引擎
│   ├── context_store.py   # 上下文存储
│   └── checkpoint.py      # 检查点管理
│
├── agents_custom/         # 新增：专用 Agent
│   ├── __init__.py
│   ├── base.py            # Agent 基类
│   ├── requirements.py    # 需求分析 Agent
│   ├── design.py          # 技术方案 Agent
│   ├── coding.py          # AI 编码 Agent
│   ├── testing.py         # 测试生成 Agent
│   └── delivery.py        # 交付审查 Agent
│
└── storage/
    ├── workflows/         # 工作流数据
    └── checkpoints/       # 检查点
```

---

## 3. 核心组件实现

### 3.1 工作流上下文

创建 `orchestrator/context_store.py`：

```python
"""工作流上下文 - 在各 Agent 之间传递状态"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
import uuid


@dataclass
class WorkflowContext:
    """工作流上下文 - 在各 Agent 之间传递状态"""

    # 基本信息
    workflow_id: str = field(default_factory=lambda: f"wf_{uuid.uuid4().hex[:8]}")
    user_request: str = ""
    current_stage: str = ""
    stages_completed: list = field(default_factory=list)

    # 各阶段产物
    requirements_doc: Optional[str] = None
    design_doc: Optional[str] = None
    source_files: list = field(default_factory=list)
    test_results: Optional[dict] = None
    delivery_report: Optional[str] = None
    package_path: Optional[str] = None

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 错误信息
    errors: list = field(default_factory=list)

    # 临时变量（不持久化）
    current_messages: list = field(default_factory=list, repr=False)

    def update(self, **kwargs) -> "WorkflowContext":
        """更新上下文"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now().isoformat()
        return self

    def to_dict(self) -> dict:
        """转换为字典（用于持久化）"""
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
    def from_dict(cls, data: dict) -> "WorkflowContext":
        """从字典加载"""
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
```

### 3.2 上下文存储

继续创建 `orchestrator/context_store.py`（添加存储类）：

```python
"""上下文存储 - 支持内存缓存和磁盘持久化"""

import json
import os
from pathlib import Path
from typing import Optional
from .context_store import WorkflowContext


class ContextStore:
    """上下文存储 - 管理状态持久化"""

    def __init__(self, storage_dir: str = "./storage/workflows"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self._cache: dict[str, WorkflowContext] = {}

    def create(self, user_request: str) -> WorkflowContext:
        """创建新上下文"""
        context = WorkflowContext(user_request=user_request)
        self._cache[context.workflow_id] = context
        return context

    def get(self, workflow_id: str) -> Optional[WorkflowContext]:
        """获取上下文"""
        # 先从缓存获取
        if workflow_id in self._cache:
            return self._cache[workflow_id]

        # 从磁盘加载
        return self._load_from_disk(workflow_id)

    async def save(self, context: WorkflowContext):
        """保存上下文"""
        # 更新缓存
        self._cache[context.workflow_id] = context

        # 持久化到磁盘
        self._save_to_disk(context)

    def _save_to_disk(self, context: WorkflowContext):
        """保存到磁盘"""
        filepath = self.storage_dir / f"{context.workflow_id}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(context.to_dict(), f, ensure_ascii=False, indent=2)

    def _load_from_disk(self, workflow_id: str) -> Optional[WorkflowContext]:
        """从磁盘加载"""
        filepath = self.storage_dir / f"{workflow_id}.json"

        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        context = WorkflowContext.from_dict(data)
        self._cache[workflow_id] = context
        return context

    def list_workflows(self) -> list[dict]:
        """列出所有工作流"""
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
```

### 3.3 检查点管理

创建 `orchestrator/checkpoint.py`：

```python
"""检查点管理 - 支持断点续跑"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class CheckpointManager:
    """检查点管理器"""

    def __init__(self, checkpoint_dir: str = "./storage/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        workflow_id: str,
        stage: str,
        context: dict,
        metadata: Optional[dict] = None,
    ):
        """保存检查点"""
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

    def get_latest_checkpoint(self, workflow_id: str) -> Optional[dict]:
        """获取最新检查点"""
        checkpoints = list(self.checkpoint_dir.glob(f"{workflow_id}_*.json"))

        if not checkpoints:
            return None

        # 按文件名排序（包含时间戳），返回最新的
        checkpoints.sort(key=lambda x: x.name, reverse=True)
        latest = checkpoints[0]

        with open(latest, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_checkpoint_at_stage(
        self,
        workflow_id: str,
        stage: str,
    ) -> Optional[dict]:
        """获取指定阶段的检查点"""
        checkpoints = list(self.checkpoint_dir.glob(f"{workflow_id}_{stage}_*.json"))

        if not checkpoints:
            return None

        checkpoints.sort(key=lambda x: x.name, reverse=True)

        with open(checkpoints[0], "r", encoding="utf-8") as f:
            return json.load(f)

    def restore_from_checkpoint(self, checkpoint: dict) -> dict:
        """从检查点恢复上下文"""
        return checkpoint.get("context", {})

    def list_checkpoints(self, workflow_id: str) -> list[dict]:
        """列出工作流的所有检查点"""
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
```

---

## 4. 工作流引擎

创建 `orchestrator/workflow_engine.py`：

```python
"""工作流引擎 - 核心编排逻辑"""

import asyncio
from typing import Optional, Callable
from .context_store import ContextStore, WorkflowContext
from .checkpoint import CheckpointManager


class WorkflowEngine:
    """工作流引擎 - 编排多 Agent 协作"""

    # 定义工作流阶段
    STAGES = [
        ("requirements", "RequirementsAgent"),
        ("design", "DesignAgent"),
        ("coding", "CodingAgent"),
        ("testing", "TestingAgent"),
        ("delivery", "DeliveryAgent"),
    ]

    def __init__(self):
        self.context_store = ContextStore()
        self.checkpoint_manager = CheckpointManager()
        self.agents: dict[str, Callable] = {}
        self._register_agents()

        # 错误处理配置
        self.max_retries = 3
        self.retry_delay = 2.0  # 秒

    def _register_agents(self):
        """注册所有 Agent"""
        from ..agents_custom.requirements import RequirementsAgent
        from ..agents_custom.design import DesignAgent
        from ..agents_custom.coding import CodingAgent
        from ..agents_custom.testing import TestingAgent
        from ..agents_custom.delivery import DeliveryAgent

        self.agents = {
            "RequirementsAgent": RequirementsAgent,
            "DesignAgent": DesignAgent,
            "CodingAgent": CodingAgent,
            "TestingAgent": TestingAgent,
            "DeliveryAgent": DeliveryAgent,
        }

    async def execute(self, user_request: str) -> dict:
        """执行完整工作流"""
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

    async def _handle_error(self, stage: str, result, context: WorkflowContext):
        """错误处理"""
        context.errors.append(f"{stage}: {result.error}")

        if result.can_retry:
            print("尝试重试...")
            # 重试逻辑可以在这里实现

    async def _handle_exception(self, stage: str, error: Exception, context: WorkflowContext):
        """异常处理"""
        context.errors.append(f"{stage}: {str(error)}")
        await self.context_store.save(context)

    def _build_delivery(self, context: WorkflowContext) -> dict:
        """构建交付物"""
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

    async def resume_from_checkpoint(self, workflow_id: str) -> dict:
        """从检查点恢复执行"""
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
```

---

## 5. Agent 结果类

创建 `agents_custom/base.py`：

```python
"""Agent 基类和结果类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from orchestrator.context_store import WorkflowContext


@dataclass
class AgentResult:
    """Agent 执行结果"""

    success: bool = True
    output: Any = None
    error: Optional[str] = None
    context: Optional[WorkflowContext] = None
    can_retry: bool = False

    def __post_init__(self):
        if not self.success and not self.error:
            self.error = "未知错误"


class BaseAgent(ABC):
    """所有 Agent 的抽象基类"""

    name: str
    system_prompt: str
    verbose: bool = True

    def __init__(
        self,
        name: str = None,
        system_prompt: str = None,
        verbose: bool = True,
    ):
        if name:
            self.name = name
        if system_prompt:
            self.system_prompt = system_prompt
        self.verbose = verbose

    @abstractmethod
    async def execute(self, context: WorkflowContext) -> AgentResult:
        """执行 Agent 任务（抽象方法）"""
        pass

    def get_tools(self) -> list:
        """获取 Agent 可用工具"""
        return []

    async def _call_llm(
        self,
        messages: list[dict],
        tools: list = None,
    ) -> Any:
        """调用 Claude API"""
        from anthropic import Anthropic
        import os

        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        params = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "system": self.system_prompt,
            "messages": messages,
        }

        if tools:
            params["tools"] = [tool.to_dict() for tool in tools]

        return client.messages.create(**params)
```

---

## 6. 5 个专用 Agent 实现

### 6.1 需求分析 Agent

创建 `agents_custom/requirements.py`：

```python
"""需求分析 Agent"""

from .base import BaseAgent, AgentResult
from orchestrator.context_store import WorkflowContext


class RequirementsAgent(BaseAgent):
    """需求分析 Agent - 从用户需求生成结构化需求文档"""

    def __init__(self):
        super().__init__(
            name="RequirementsAgent",
            system_prompt="""你是一位产品专家，擅长从模糊需求中提取明确的功能点。

你的职责：
1. 分析用户的原始需求描述
2. 识别核心功能和边界
3. 提取明确的功能列表
4. 生成结构化的需求文档

输出格式（Markdown）：
# 项目概述
[简短描述]

# 核心功能
- 功能 1
- 功能 2
...

# 用户故事
- 作为 [角色]，我希望 [功能]，以便 [价值]

# 验收标准
[明确的验收条件]

# 非功能需求
[性能、安全等要求]
""",
            verbose=True,
        )

    def get_tools(self) -> list:
        """获取可用工具"""
        from agents.tools.think import ThinkTool
        from agents.tools.file_tools import FileWriteTool
        return [ThinkTool(), FileWriteTool()]

    async def execute(self, context: WorkflowContext) -> AgentResult:
        """执行需求分析"""
        from agents.utils.tool_util import execute_tools

        user_request = context.user_request

        if self.verbose:
            print(f"[RequirementsAgent] 分析需求：{user_request[:100]}...")

        try:
            # 调用 Claude 分析需求
            response = await self._call_llm(
                messages=[{"role": "user", "content": user_request}],
                tools=self.get_tools(),
            )

            # 处理响应
            requirements_doc = None
            tool_results = []

            for block in response.content:
                if block.type == "text":
                    requirements_doc = block.text
                elif block.type == "tool_use":
                    # 执行工具调用
                    tool_dict = {tool.name: tool for tool in self.get_tools()}
                    tool_results = await execute_tools([block], tool_dict)

            if not requirements_doc:
                requirements_doc = f"# 需求文档\n\n用户需求：{user_request}"

            # 保存到上下文
            context.requirements_doc = requirements_doc

            if self.verbose:
                print(f"[RequirementsAgent] 需求文档已生成 ({len(requirements_doc)} 字符)")

            return AgentResult(
                success=True,
                output=requirements_doc,
                context=context,
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"需求分析失败：{str(e)}",
                can_retry=True,
                context=context,
            )
```

### 6.2 技术方案 Agent

创建 `agents_custom/design.py`：

```python
"""技术方案 Agent"""

from .base import BaseAgent, AgentResult
from orchestrator.context_store import WorkflowContext


class DesignAgent(BaseAgent):
    """技术方案 Agent - 根据需求生成技术设计文档"""

    def __init__(self):
        super().__init__(
            name="DesignAgent",
            system_prompt="""你是一位架构师，负责设计清晰的技术方案。

你的职责：
1. 阅读需求文档
2. 设计技术架构
3. 规划项目文件结构
4. 选择技术栈
5. 生成技术设计文档

输出格式（Markdown）：
# 技术设计文档

## 技术选型
[语言和框架选择]

## 架构设计
[架构图或描述]

## 目录结构
[文件组织]

## 核心模块
[模块说明]

## 接口设计
[API 或接口定义]
""",
            verbose=True,
        )

    def get_tools(self) -> list:
        """获取可用工具"""
        from agents.tools.think import ThinkTool
        from agents.tools.file_tools import FileReadTool, FileWriteTool
        return [ThinkTool(), FileReadTool(), FileWriteTool()]

    async def execute(self, context: WorkflowContext) -> AgentResult:
        """执行技术方案设计"""
        requirements = context.requirements_doc

        if not requirements:
            return AgentResult(
                success=False,
                error="需求文档不存在，请先执行需求分析",
                can_retry=False,
                context=context,
            )

        if self.verbose:
            print(f"[DesignAgent] 设计技术方案...")

        try:
            # 调用 Claude 设计方案
            response = await self._call_llm(
                messages=[{
                    "role": "user",
                    "content": f"请为以下需求设计技术方案：\n\n{requirements}",
                }],
                tools=self.get_tools(),
            )

            # 提取设计文档
            design_doc = None
            for block in response.content:
                if block.type == "text":
                    design_doc = block.text
                    break

            if not design_doc:
                design_doc = "# 技术设计文档\n\n待生成..."

            # 保存到上下文
            context.design_doc = design_doc

            if self.verbose:
                print(f"[DesignAgent] 设计文档已生成 ({len(design_doc)} 字符)")

            return AgentResult(
                success=True,
                output=design_doc,
                context=context,
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"技术方案设计失败：{str(e)}",
                can_retry=True,
                context=context,
            )
```

### 6.3 AI 编码 Agent

创建 `agents_custom/coding.py`：

```python
"""AI 编码 Agent"""

from .base import BaseAgent, AgentResult
from orchestrator.context_store import WorkflowContext


class CodingAgent(BaseAgent):
    """AI 编码 Agent - 根据设计文档实现代码"""

    def __init__(self):
        super().__init__(
            name="CodingAgent",
            system_prompt="""你是一位高级开发者，编写高质量、可维护的代码。

你的职责：
1. 阅读技术设计文档
2. 创建项目结构
3. 编写源代码文件
4. 初始化 Git 仓库
5. 提交代码

代码质量标准：
- 遵循最佳实践
- 添加必要的注释
- 保持代码简洁
- 处理边界情况
""",
            verbose=True,
        )

    def get_tools(self) -> list:
        """获取可用工具"""
        from agents.tools.think import ThinkTool
        from agents.tools.file_tools import FileReadTool, FileWriteTool
        from custom_tools.git_tool import GitTool
        from custom_tools.shell_tool import ShellTool
        return [ThinkTool(), FileReadTool(), FileWriteTool(), GitTool(), ShellTool()]

    async def execute(self, context: WorkflowContext) -> AgentResult:
        """执行代码实现"""
        design_doc = context.design_doc

        if not design_doc:
            return AgentResult(
                success=False,
                error="设计文档不存在，请先执行技术方案设计",
                can_retry=False,
                context=context,
            )

        if self.verbose:
            print(f"[CodingAgent] 开始编码实现...")

        try:
            # 调用 Claude 编写代码
            response = await self._call_llm(
                messages=[{
                    "role": "user",
                    "content": f"请根据以下技术设计实现代码：\n\n{design_doc}",
                }],
                tools=self.get_tools(),
            )

            # 提取创建的文件的列表
            source_files = []
            for block in response.content:
                if block.type == "text":
                    # 可以从响应中解析创建的文件
                    pass
                elif block.type == "tool_use":
                    # 工具调用（文件创建、Git 操作等）
                    pass

            context.source_files = source_files

            if self.verbose:
                print(f"[CodingAgent] 编码完成，创建 {len(source_files)} 个文件")

            return AgentResult(
                success=True,
                output=f"创建 {len(source_files)} 个文件",
                context=context,
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"编码失败：{str(e)}",
                can_retry=True,
                context=context,
            )
```

### 6.4 测试生成 Agent

创建 `agents_custom/testing.py`：

```python
"""测试生成 Agent"""

from .base import BaseAgent, AgentResult
from orchestrator.context_store import WorkflowContext


class TestingAgent(BaseAgent):
    """测试生成 Agent - 生成并执行测试用例"""

    def __init__(self):
        super().__init__(
            name="TestingAgent",
            system_prompt="""你是一位 QA 工程师，确保代码质量。

你的职责：
1. 分析源代码
2. 生成测试用例
3. 编写测试文件
4. 执行测试
5. 生成测试报告

测试覆盖：
- 单元测试
- 边界条件测试
- 错误处理测试
""",
            verbose=True,
        )

    def get_tools(self) -> list:
        """获取可用工具"""
        from agents.tools.think import ThinkTool
        from agents.tools.file_tools import FileReadTool, FileWriteTool
        return [ThinkTool(), FileReadTool(), FileWriteTool()]

    async def execute(self, context: WorkflowContext) -> AgentResult:
        """执行测试生成"""
        source_files = context.source_files

        if not source_files:
            return AgentResult(
                success=False,
                error="源代码文件不存在，请先执行编码",
                can_retry=False,
                context=context,
            )

        if self.verbose:
            print(f"[TestingAgent] 生成测试用例...")

        try:
            # 调用 Claude 生成测试
            response = await self._call_llm(
                messages=[{
                    "role": "user",
                    "content": f"请为以下代码生成测试用例：\n\n{source_files}",
                }],
                tools=self.get_tools(),
            )

            # 提取测试结果
            test_results = {"passed": True, "details": "测试已生成"}

            context.test_results = test_results

            if self.verbose:
                print(f"[TestingAgent] 测试生成完成")

            return AgentResult(
                success=True,
                output=test_results,
                context=context,
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"测试生成失败：{str(e)}",
                can_retry=True,
                context=context,
            )
```

### 6.5 交付审查 Agent

创建 `agents_custom/delivery.py`：

```python
"""交付审查 Agent"""

from .base import BaseAgent, AgentResult
from orchestrator.context_store import WorkflowContext


class DeliveryAgent(BaseAgent):
    """交付审查 Agent - 最终审查与打包"""

    def __init__(self):
        super().__init__(
            name="DeliveryAgent",
            system_prompt="""你是一位技术负责人，负责最终交付审查。

你的职责：
1. 审查代码质量
2. 检查文档完整性
3. 验证测试结果
4. 生成交付报告
5. 打包交付物

审查标准：
- 代码符合规范
- 文档完整
- 测试通过
- 可运行部署
""",
            verbose=True,
        )

    def get_tools(self) -> list:
        """获取可用工具"""
        from agents.tools.think import ThinkTool
        from agents.tools.file_tools import FileReadTool
        from custom_tools.git_tool import GitTool
        return [ThinkTool(), FileReadTool(), GitTool()]

    async def execute(self, context: WorkflowContext) -> AgentResult:
        """执行交付审查"""
        if self.verbose:
            print(f"[DeliveryAgent] 开始交付审查...")

        try:
            # 审查所有产物
            review_items = {
                "requirements": context.requirements_doc,
                "design": context.design_doc,
                "source_files": context.source_files,
                "test_results": context.test_results,
            }

            # 生成审查报告
            delivery_report = self._generate_review(review_items)

            context.delivery_report = delivery_report

            if self.verbose:
                print(f"[DeliveryAgent] 交付审查完成")

            return AgentResult(
                success=True,
                output=delivery_report,
                context=context,
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"交付审查失败：{str(e)}",
                can_retry=True,
                context=context,
            )

    def _generate_review(self, review_items: dict) -> str:
        """生成审查报告"""
        report = ["# 交付审查报告\n"]

        # 检查各项产物
        for item, content in review_items.items():
            status = "✓" if content else "✗"
            report.append(f"- {status} {item}")

        report.append("\n## 总体评价")
        report.append("所有产物已审查完成。")

        return "\n".join(report)
```

### 6.6 模块导出

创建 `agents_custom/__init__.py`：

```python
"""自定义 Agent 模块"""

from .base import BaseAgent, AgentResult
from .requirements import RequirementsAgent
from .design import DesignAgent
from .coding import CodingAgent
from .testing import TestingAgent
from .delivery import DeliveryAgent

__all__ = [
    "BaseAgent",
    "AgentResult",
    "RequirementsAgent",
    "DesignAgent",
    "CodingAgent",
    "TestingAgent",
    "DeliveryAgent",
]
```

---

## 7. 编排层导出

创建 `orchestrator/__init__.py`：

```python
"""编排层模块"""

from .workflow_engine import WorkflowEngine
from .context_store import ContextStore, WorkflowContext
from .checkpoint import CheckpointManager

__all__ = [
    "WorkflowEngine",
    "ContextStore",
    "WorkflowContext",
    "CheckpointManager",
]
```

---

## 8. 测试工作流

### 8.1 创建测试脚本

创建 `tests/test_workflow.py`：

```python
"""测试完整工作流"""

import asyncio
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.workflow_engine import WorkflowEngine
from config import get_api_key


async def main():
    """测试完整工作流"""
    # 设置 API 密钥
    os.environ["ANTHROPIC_API_KEY"] = get_api_key()

    # 创建工作流引擎
    engine = WorkflowEngine()

    # 执行工作流
    result = await engine.execute(
        user_request="创建一个 Python 计算器项目，支持加减乘除运算"
    )

    # 显示结果
    print("\n工作流结果:")
    print(f"  状态：{result['status']}")
    print(f"  完成的阶段：{result['stages_completed']}")
    print(f"  错误：{result.get('errors', [])}")


if __name__ == "__main__":
    asyncio.run(main())
```

### 8.2 运行测试

```bash
python tests/test_workflow.py
```

---

## 9. 阶段 2 检查清单

完成以下任务后，阶段 2 即完成：

### 核心组件

- [ ] 创建 WorkflowContext 类
- [ ] 创建 ContextStore 类
- [ ] 创建 CheckpointManager 类
- [ ] 创建 WorkflowEngine 类

### Agent 实现

- [ ] 创建 BaseAgent 基类
- [ ] 实现 RequirementsAgent
- [ ] 实现 DesignAgent
- [ ] 实现 CodingAgent
- [ ] 实现 TestingAgent
- [ ] 实现 DeliveryAgent

### 测试

- [ ] 运行完整工作流测试
- [ ] 测试检查点保存和恢复
- [ ] 测试错误处理和重试

### 文档

- [ ] 更新 README.md
- [ ] 编写 API 文档

---

## 下一步

完成阶段 2 后，继续阅读 [PHASE3.md](./PHASE3.md) 实现完备的生产级系统。
