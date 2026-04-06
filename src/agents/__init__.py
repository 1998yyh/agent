"""Agent 模块"""

__all__ = ["Agent", "Tool"]

# 延迟导入避免循环依赖
def __getattr__(name):
    if name == "Agent":
        from .agent import Agent
        return Agent
    elif name == "Tool":
        from .tools.base import Tool
        return Tool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
