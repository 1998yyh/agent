"""AI 编码 Agent - 根据设计文档实现代码"""

from ..agents.tools.think import ThinkTool
from ..agents.tools.file_tools import FileReadTool, FileWriteTool
from ..tools.git_tool import GitTool
from ..tools.shell_tool import ShellTool
from ..orchestrator.context_store import WorkflowContext
from .base import BaseAgent, AgentResult


class CodingAgent(BaseAgent):
    """AI 编码 Agent - 根据设计文档实现代码

    职责：
    1. 阅读技术设计文档
    2. 创建项目结构
    3. 编写源代码文件
    4. 初始化 Git 仓库
    5. 提交代码
    """

    def __init__(self, verbose: bool = True):
        """初始化 AI 编码 Agent

        Args:
            verbose: 是否启用详细日志
        """
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
            verbose=verbose,
        )

    def get_tools(self) -> list:
        """获取可用工具

        Returns:
            工具列表
        """
        return [
            ThinkTool(),
            FileReadTool(),
            FileWriteTool(),
            GitTool(),
            ShellTool(),
        ]

    async def execute(self, context: WorkflowContext) -> AgentResult:
        """执行代码实现

        Args:
            context: 工作流上下文

        Returns:
            Agent 执行结果
        """
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

            # 提取创建的文件列表
            source_files = []
            for block in response.content:
                if block.type == "tool_use" and block.name in ["file_write", "file_write_tool"]:
                    if "path" in block.input:
                        source_files.append(block.input["path"])

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
