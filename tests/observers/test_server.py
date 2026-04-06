"""ObserverServer WebSocket 服务器单元测试"""

import pytest
import asyncio
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from observers.server import ObserverServer


@pytest.mark.asyncio
async def test_server_init():
    """测试服务器初始化"""
    server = ObserverServer(host="127.0.0.1", port=8766)
    assert server.host == "127.0.0.1"
    assert server.port == 8766
    assert server.clients == set()
    assert server.client_count == 0


@pytest.mark.asyncio
async def test_server_default_port():
    """测试默认端口"""
    server = ObserverServer()
    assert server.port == 8765


@pytest.mark.asyncio
async def test_server_broadcast_no_clients():
    """测试没有客户端时的广播"""
    server = ObserverServer(port=8768)
    # 不应该抛出异常
    await server.broadcast({"type": "test", "data": {}})


@pytest.mark.asyncio
async def test_server_stop():
    """测试停止服务器"""
    server = ObserverServer(port=8769)
    # 启动后台服务器
    task = asyncio.create_task(server.start_background())
    await asyncio.sleep(0.5)

    # 停止服务器
    await server.stop()

    # 验证客户端集合被清空
    assert server.clients == set()

    # 取消任务
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
