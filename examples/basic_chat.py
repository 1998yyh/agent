"""基础对话示例"""

import asyncio
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent import Agent
from agents.tools.think import ThinkTool
from utils.config import get_api_key


async def main():
    """基础对话示例"""
    # 设置 API 密钥
    os.environ["ANTHROPIC_API_KEY"] = get_api_key()

    # 创建简单 Agent
    print("创建 ChatAgent...")
    agent = Agent(
        name="ChatAgent",
        system="你是一个友好的聊天助手。请用简洁的方式回答问题。",
        tools=[ThinkTool()],
        verbose=True,
    )

    # 测试对话
    print("\n测试对话:")
    print("-" * 40)

    questions = [
        "你好，请介绍一下自己",
        "Python 和 JavaScript 有什么区别？",
        "如何学习编程？",
    ]

    for question in questions:
        print(f"\n问：{question}")
        response = await agent.run_async(question)

        for block in response.content:
            if block.type == "text":
                print(f"答：{block.text[:200]}...")

        print("-" * 40)

    print("\n示例完成！")


if __name__ == "__main__":
    asyncio.run(main())
