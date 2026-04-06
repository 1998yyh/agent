"""Agent 模块单元测试"""

import pytest
from agents.agent import Agent, ModelConfig
from agents.tools.think import ThinkTool


class TestModelConfig:
    """ModelConfig 测试类"""

    def test_model_config_default(self):
        """测试默认配置"""
        config = ModelConfig()

        assert config.model == "glm-5"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.context_window_tokens == 180000

    def test_model_config_custom(self):
        """测试自定义配置"""
        config = ModelConfig(
            model="claude-opus-4-20250514",
            max_tokens=2048,
            temperature=0.5,
        )

        assert config.model == "claude-opus-4-20250514"
        assert config.max_tokens == 2048
        assert config.temperature == 0.5


class TestAgent:
    """Agent 测试类"""

    def test_agent_init(self):
        """测试 Agent 初始化"""
        agent = Agent(
            name="TestAgent",
            system="测试系统提示词",
            tools=[ThinkTool()],
        )

        assert agent.name == "TestAgent"
        assert agent.system == "测试系统提示词"
        assert len(agent.tools) == 1
        assert agent.config is not None

    def test_agent_init_with_config(self):
        """测试使用自定义配置初始化 Agent"""
        config = ModelConfig(model="claude-opus-4-20250514")

        agent = Agent(
            name="TestAgent",
            system="测试",
            config=config,
        )

        assert agent.config.model == "claude-opus-4-20250514"

    def test_agent_init_without_tools(self):
        """测试没有工具时初始化 Agent"""
        agent = Agent(
            name="TestAgent",
            system="测试",
        )

        assert agent.tools == []

    def test_agent_prepare_message_params(self):
        """测试准备消息参数"""
        agent = Agent(
            name="TestAgent",
            system="测试",
            tools=[ThinkTool()],
        )

        params = agent._prepare_message_params()

        assert "model" in params
        assert "max_tokens" in params
        assert "system" in params
        assert "messages" in params
        assert "tools" in params
        assert len(params["tools"]) == 1
