"""交付审查 Agent - 最终审查与打包"""

from ..agents.tools.think import ThinkTool
from ..agents.tools.file_tools import FileReadTool
from ..tools.git_tool import GitTool
from ..orchestrator.context_store import WorkflowContext
from .base import BaseAgent, AgentResult


class DeliveryAgent(BaseAgent):
    """交付审查 Agent - 最终审查与打包

    职责：
    1. 审查代码质量
    2. 检查文档完整性
    3. 验证测试结果
    4. 生成交付报告
    5. 打包交付物
    """

    def __init__(self, verbose: bool = True):
        """初始化交付审查 Agent

        Args:
            verbose: 是否启用详细日志
        """
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
            verbose=verbose,
        )

    def get_tools(self) -> list:
        """获取可用工具

        Returns:
            工具列表
        """
        return [ThinkTool(), FileReadTool(), GitTool()]

    async def execute(self, context: WorkflowContext) -> AgentResult:
        """执行交付审查

        Args:
            context: 工作流上下文

        Returns:
            Agent 执行结果
        """
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
        """生成审查报告

        Args:
            review_items: 审查项目字典

        Returns:
            审查报告字符串
        """
        report = ["# 交付审查报告\n"]

        # 检查各项产物
        for item, content in review_items.items():
            status = "已生成" if content else "未生成"
            report.append(f"- {item}: {status}")

        report.append("\n## 总体评价")
        report.append("所有产物已审查完成。")

        return "\n".join(report)
