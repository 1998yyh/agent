"""Pytest 配置和共享 fixtures"""

import pytest
import os
import sys
import tempfile

# 添加 src 到路径，使测试可以导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def api_key():
    """获取测试 API 密钥"""
    return os.environ.get("ANTHROPIC_API_KEY", "test-key")
