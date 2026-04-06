"""工具执行工具 - 支持并行执行"""

import asyncio
from typing import Any


async def _execute_single_tool(
    call: Any, tool_dict: dict[str, Any]
) -> dict[str, Any]:
    """执行单个工具并处理错误"""
    response = {"type": "tool_result", "tool_use_id": call.id}

    try:
        # 直接执行工具
        result = await tool_dict[call.name].execute(**call.input)
        response["content"] = str(result)
    except KeyError:
        response["content"] = f"未找到工具 '{call.name}'"
        response["is_error"] = True
    except Exception as e:
        response["content"] = f"工具执行错误：{str(e)}"
        response["is_error"] = True

    return response


async def execute_tools(
    tool_calls: list[Any], tool_dict: dict[str, Any], parallel: bool = True
) -> list[dict[str, Any]]:
    """顺序或并行执行多个工具

    参数:
        tool_calls: 工具调用列表
        tool_dict: 工具字典
        parallel: 是否并行执行（默认 True）

    返回:
        工具结果列表
    """
    if parallel:
        # 并行执行所有工具
        return await asyncio.gather(
            *[_execute_single_tool(call, tool_dict) for call in tool_calls]
        )
    else:
        # 顺序执行工具
        return [
            await _execute_single_tool(call, tool_dict) for call in tool_calls
        ]
