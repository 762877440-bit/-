# config.py
import os
from dataclasses import dataclass, field
from typing import Optional
import yaml


@dataclass
class ModelConfig:
    endpoint: str = "http://localhost:11434/api/generate"
    name: str = "qwen3.5-4b"
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = True


@dataclass
class MemoryConfig:
    vector_db_path: str = "./chroma_db"
    mem0_config: dict = None


@dataclass
class SearchConfig:
    engine: str = "duckduckgo"
    timeout: int = 5
    max_results: int = 5


@dataclass
class AgentConfig:
    verbose: bool = False
    max_iterations: int = 5


@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)


def load_config(path: str = "config.yaml") -> Config:
    """从 YAML 文件加载配置，支持环境变量覆盖"""
    config = Config()
    
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        # 加载模型配置
        if 'model' in yaml_data:
            model_data = yaml_data['model']
            config.model.endpoint = model_data.get('endpoint', config.model.endpoint)
            config.model.name = model_data.get('name', config.model.name)
            config.model.temperature = float(model_data.get('temperature', config.model.temperature))
            config.model.max_tokens = int(model_data.get('max_tokens', config.model.max_tokens))
            config.model.stream = bool(model_data.get('stream', config.model.stream))
        
        # 加载记忆配置
        if 'memory' in yaml_data:
            memory_data = yaml_data['memory']
            config.memory.vector_db_path = memory_data.get('vector_db_path', config.memory.vector_db_path)
            config.memory.mem0_config = memory_data.get('mem0_config', {})
        
        # 加载搜索配置
        if 'search' in yaml_data:
            search_data = yaml_data['search']
            config.search.engine = search_data.get('engine', config.search.engine)
            config.search.timeout = int(search_data.get('timeout', config.search.timeout))
            config.search.max_results = int(search_data.get('max_results', config.search.max_results))
        
        # 加载Agent配置
        if 'agent' in yaml_data:
            agent_data = yaml_data['agent']
            config.agent.verbose = bool(agent_data.get('verbose', config.agent.verbose))
            config.agent.max_iterations = int(agent_data.get('max_iterations', config.agent.max_iterations))
    
    # 环境变量覆盖
    if os.getenv('MODEL_ENDPOINT'):
        config.model.endpoint = os.getenv('MODEL_ENDPOINT')
    if os.getenv('MODEL_NAME'):
        config.model.name = os.getenv('MODEL_NAME')
    if os.getenv('SEARCH_ENGINE'):
        config.search.engine = os.getenv('SEARCH_ENGINE')
    
    return config