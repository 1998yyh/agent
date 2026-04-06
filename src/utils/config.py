"""DevAgent 配置管理"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    """模型配置"""

    model: str = "glm-5"  # 默认模型
    max_tokens: int = 4096  # 最大生成 token
    temperature: float = 0.7  # 温度参数
    context_window_tokens: int = 180000  # 上下文窗口 token 限制
    base_url: Optional[str] = None  # API 基础地址，可选


@dataclass
class AgentConfig:
    """Agent 配置"""

    name: str = "DevAgent"
    verbose: bool = True
    system_prompt: Optional[str] = None


@dataclass
class ToolConfig:
    """工具配置"""

    # Git 工具配置
    git_author_name: str = "DevAgent"
    git_author_email: str = "devagent@local"

    # Shell 工具配置
    shell_timeout: int = 60  # 秒

    # 文件工具配置
    max_file_size: int = 1024 * 1024  # 1MB


# 阿里云百炼默认配置
DEFAULT_DASHSCOPE_BASE_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic"
# 注意：API 密钥应通过环境变量设置，不应硬编码


def load_env():
    """加载环境变量"""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file)


def get_model_from_env() -> str:
    """从环境变量读取模型名称

    Returns:
        模型名称，默认返回 glm-5
    """
    return os.environ.get("ANTHROPIC_MODEL", "glm-5")


def get_base_url_from_env() -> Optional[str]:
    """从环境变量读取 API 基础地址

    Returns:
        API 基础地址，默认返回阿里云百炼地址
    """
    return os.environ.get(
        "ANTHROPIC_BASE_URL",
        DEFAULT_DASHSCOPE_BASE_URL
    )


def get_api_key_from_env() -> str:
    """从环境变量读取 API 密钥

    Returns:
        API 密钥，如果未设置则抛出异常
    """
    # 优先使用 ANTHROPIC_API_KEY，其次使用 DASHSCOPE_API_KEY
    api_key = os.environ.get(
        "ANTHROPIC_API_KEY",
        os.environ.get("DASHSCOPE_API_KEY", "")
    )
    return api_key


def get_model_config() -> ModelConfig:
    """获取模型配置

    Returns:
        ModelConfig 实例，从环境变量读取配置
    """
    return ModelConfig(
        model=get_model_from_env(),
        max_tokens=4096,
        temperature=0.7,
        base_url=get_base_url_from_env(),
    )


def get_api_key() -> str:
    """获取 API 密钥"""
    api_key = get_api_key_from_env()
    if not api_key:
        raise ValueError(
            "请设置 ANTHROPIC_API_KEY 或 DASHSCOPE_API_KEY 环境变量 "
            "或创建 .env 文件"
        )
    return api_key


# 默认配置实例
DEFAULT_MODEL_CONFIG = ModelConfig()
DEFAULT_AGENT_CONFIG = AgentConfig()
DEFAULT_TOOL_CONFIG = ToolConfig()
