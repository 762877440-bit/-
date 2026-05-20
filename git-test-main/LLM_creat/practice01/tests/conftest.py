# tests/conftest.py
import pytest
from unittest.mock import MagicMock
from memory_system import EphemeralMemorySystem


@pytest.fixture
def mock_model_client():
    """创建模拟的模型客户端"""
    client = MagicMock()
    client.generate.return_value = "模拟回复"
    # 异步方法需要设置return_value为协程
    async def mock_generate(*args, **kwargs):
        return "模拟回复"
    client.generate = mock_generate
    return client


@pytest.fixture
def mock_search_tool():
    """创建模拟的搜索工具"""
    async def mock_search_and_format(*args, **kwargs):
        return "模拟搜索结果"
    
    tool = MagicMock()
    tool.search_and_format = mock_search_and_format
    return tool


@pytest.fixture
def temp_memory_system():
    """创建临时内存记忆系统"""
    return EphemeralMemorySystem()


@pytest.fixture
def config_yaml(tmp_path):
    """创建临时配置文件"""
    config = {
        "model": {
            "endpoint": "http://localhost:11434/api/generate",
            "name": "qwen3.4-4b",
            "temperature": 0.7,
            "max_tokens": 2048,
            "stream": True
        },
        "memory": {
            "vector_db_path": str(tmp_path / "memory")
        },
        "search": {
            "engine": "duckduckgo",
            "timeout": 5,
            "max_results": 5
        },
        "agent": {
            "verbose": False,
            "max_iterations": 5
        }
    }
    
    import yaml
    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    return str(config_file)