"""Agent 工厂 - 支持为不同 Agent 配置不同模型"""

from typing import Any, Optional

from utils.config import ModelConfig
from .agent import Agent
from .tools.base import Tool


class AgentFactory:
    """Agent 工厂类，支持为不同 Agent 配置不同模型

    使用示例:
        # 创建默认 Agent
        agent = AgentFactory.create_agent("default")

        # 创建带自定义模型配置的 Agent
        agent = AgentFactory.create_agent(
            "coding",
            ModelConfig(model="claude-sonnet-4-20250514")
        )

        # 使用预设的 Agent 类型
        coding_agent = AgentFactory.create_coding_agent()
        design_agent = AgentFactory.create_design_agent()
    """

    # 预设的 Agent 类型和模型映射
    AGENT_MODEL_MAPPING = {
        "default": "claude-sonnet-4-20250514",
        "coding": "claude-sonnet-4-20250514",
        "design": "claude-opus-4-20250514",
        "requirements": "claude-opus-4-20250514",
        "testing": "claude-haiku-4-5-20251001",
        "review": "claude-sonnet-4-20250514",
    }

    @staticmethod
    def create_agent(
        name: str,
        system: str,
        tools: Optional[list[Tool]] = None,
        mcp_servers: Optional[list[dict[str, Any]]] = None,
        model_config: Optional[ModelConfig] = None,
        verbose: bool = False,
    ) -> Agent:
        """创建指定配置的 Agent

        Args:
            name: Agent 标识符
            system: Agent 的系统提示词
            tools: Agent 可使用的工具列表
            mcp_servers: MCP 服务器配置
            model_config: 模型配置，不传则使用默认配置
            verbose: 是否启用详细日志

        Returns:
            Agent 实例
        """
        return Agent(
            name=name,
            system=system,
            tools=tools,
            mcp_servers=mcp_servers,
            config=model_config,
            verbose=verbose,
        )

    @staticmethod
    def create_agent_by_type(
        agent_type: str,
        system: Optional[str] = None,
        tools: Optional[list[Tool]] = None,
        verbose: bool = False,
    ) -> Agent:
        """根据 Agent 类型创建预设配置的 Agent

        Args:
            agent_type: Agent 类型 (coding, design, testing, review 等)
            system: 系统提示词，不传则使用默认提示词
            tools: 工具列表，不传则使用空列表
            verbose: 是否启用详细日志

        Returns:
            预设配置的 Agent 实例
        """
        # 获取预设模型
        model_name = AgentFactory.AGENT_MODEL_MAPPING.get(
            agent_type,
            AgentFactory.AGENT_MODEL_MAPPING["default"],
        )
        model_config = ModelConfig(model=model_name)

        # 默认系统提示词
        if system is None:
            system = f"你是一个专业的{agent_type}助手。"

        return AgentFactory.create_agent(
            name=f"{agent_type.capitalize()}Agent",
            system=system,
            tools=tools,
            model_config=model_config,
            verbose=verbose,
        )

    @staticmethod
    def create_coding_agent(
        tools: Optional[list[Tool]] = None,
        verbose: bool = False,
    ) -> Agent:
        """创建编码 Agent，使用 Sonnet 模型

        Args:
            tools: 工具列表
            verbose: 是否启用详细日志

        Returns:
            编码 Agent 实例
        """
        return AgentFactory.create_agent_by_type(
            "coding",
            system="""你是一个专业的编码助手。你可以帮助用户:

1. 编写和修改代码
2. 创建项目结构
3. 重构和优化代码
4. 解释代码逻辑

请写出清晰、可维护的代码，遵循最佳实践。""",
            tools=tools,
            verbose=verbose,
        )

    @staticmethod
    def create_design_agent(
        tools: Optional[list[Tool]] = None,
        verbose: bool = False,
    ) -> Agent:
        """创建设计 Agent，使用 Opus 模型

        Args:
            tools: 工具列表
            verbose: 是否启用详细日志

        Returns:
            设计 Agent 实例
        """
        return AgentFactory.create_agent_by_type(
            "design",
            system="""你是一个专业的软件设计助手。你可以帮助用户:

1. 设计系统架构
2. 制定技术方案
3. 设计 API 和数据结构
4. 进行技术选型

请提供清晰、可扩展的设计方案。""",
            tools=tools,
            verbose=verbose,
        )

    @staticmethod
    def create_testing_agent(
        tools: Optional[list[Tool]] = None,
        verbose: bool = False,
    ) -> Agent:
        """创建测试 Agent，使用 Haiku 模型

        Args:
            tools: 工具列表
            verbose: 是否启用详细日志

        Returns:
            测试 Agent 实例
        """
        return AgentFactory.create_agent_by_type(
            "testing",
            system="""你是一个专业的测试助手。你可以帮助用户:

1. 编写单元测试
2. 编写集成测试
3. 生成测试数据
4. 分析测试覆盖率

请编写全面、高效的测试用例。""",
            tools=tools,
            verbose=verbose,
        )

    @staticmethod
    def create_review_agent(
        tools: Optional[list[Tool]] = None,
        verbose: bool = False,
    ) -> Agent:
        """创建代码审查 Agent，使用 Sonnet 模型

        Args:
            tools: 工具列表
            verbose: 是否启用详细日志

        Returns:
            代码审查 Agent 实例
        """
        return AgentFactory.create_agent_by_type(
            "review",
            system="""你是一个专业的代码审查助手。你可以帮助用户:

1. 审查代码质量
2. 发现潜在 bug
3. 提出优化建议
4. 检查安全漏洞

请提供详细、建设性的审查意见。""",
            tools=tools,
            verbose=verbose,
        )
