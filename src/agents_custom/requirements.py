"""需求分析 Agent - 从用户需求生成结构化需求文档"""

from typing import Any

from ..agents.tools.think import ThinkTool
from ..agents.tools.file_tools import FileWriteTool
from ..orchestrator.context_store import WorkflowContext
from .base import BaseAgent, AgentResult


class RequirementsAgent(BaseAgent):
    """需求分析 Agent - 从用户需求生成结构化需求文档

    职责：
    1. 分析用户的原始需求描述
    2. 识别核心功能和边界
    3. 提取明确的功能列表
    4. 生成结构化的需求文档
    """

    def __init__(self, verbose: bool = True):
        """初始化需求分析 Agent

        Args:
            verbose: 是否启用详细日志
        """
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
            verbose=verbose,
        )

    def get_tools(self) -> list:
        """获取可用工具

        Returns:
            工具列表
        """
        return [ThinkTool(), FileWriteTool()]

    async def execute(self, context: WorkflowContext) -> AgentResult:
        """执行需求分析

        Args:
            context: 工作流上下文

        Returns:
            Agent 执行结果
        """
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
                    from ..agents.utils.tool_util import execute_tools
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
