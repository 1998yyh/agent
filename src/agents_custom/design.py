"""技术方案 Agent - 根据需求生成技术设计文档"""

from ..agents.tools.think import ThinkTool
from ..agents.tools.file_tools import FileReadTool, FileWriteTool
from ..orchestrator.context_store import WorkflowContext
from .base import BaseAgent, AgentResult


class DesignAgent(BaseAgent):
    """技术方案 Agent - 根据需求生成技术设计文档

    职责：
    1. 阅读需求文档
    2. 设计技术架构
    3. 规划项目文件结构
    4. 选择技术栈
    5. 生成技术设计文档
    """

    def __init__(self, verbose: bool = True):
        """初始化技术方案 Agent

        Args:
            verbose: 是否启用详细日志
        """
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
            verbose=verbose,
        )

    def get_tools(self) -> list:
        """获取可用工具

        Returns:
            工具列表
        """
        return [ThinkTool(), FileReadTool(), FileWriteTool()]

    async def execute(self, context: WorkflowContext) -> AgentResult:
        """执行技术方案设计

        Args:
            context: 工作流上下文

        Returns:
            Agent 执行结果
        """
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
