# tests/test_config.py
import os
import pytest
import yaml
from config import load_config, Config


def test_load_valid_config(tmp_path):
    """测试加载有效的config.yaml文件"""
    config_data = {
        "model": {
            "endpoint": "http://localhost:8080/api",
            "name": "test-model",
            "temperature": 0.5,
            "max_tokens": 1024,
            "stream": True
        },
        "memory": {
            "vector_db_path": "./test_db"
        },
        "search": {
            "engine": "duckduckgo",
            "timeout": 10,
            "max_results": 3
        },
        "agent": {
            "verbose": True,
            "max_iterations": 3
        }
    }
    
    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    
    config = load_config(str(config_file))
    
    assert config.model.endpoint == "http://localhost:8080/api"
    assert config.model.name == "test-model"
    assert config.model.temperature == 0.5
    assert config.model.max_tokens == 1024
    assert config.model.stream == True
    assert config.memory.vector_db_path == "./test_db"
    assert config.search.engine == "duckduckgo"
    assert config.search.timeout == 10
    assert config.search.max_results == 3
    assert config.agent.verbose == True
    assert config.agent.max_iterations == 3


def test_missing_config_uses_defaults():
    """测试缺失配置文件时使用默认值"""
    config = load_config("non_existent.yaml")
    
    assert config.model.endpoint == "http://localhost:11434/api/generate"
    assert config.model.name == "qwen3.4-4b"
    assert config.model.temperature == 0.7
    assert config.model.max_tokens == 2048
    assert config.model.stream == True


def test_env_var_overrides_config(tmp_path):
    """测试环境变量覆盖配置文件"""
    config_data = {
        "model": {
            "endpoint": "http://localhost:8080/api"
        }
    }
    
    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    
    os.environ['MODEL_ENDPOINT'] = "http://localhost:9090/api"
    
    try:
        config = load_config(str(config_file))
        assert config.model.endpoint == "http://localhost:9090/api"
    finally:
        del os.environ['MODEL_ENDPOINT']