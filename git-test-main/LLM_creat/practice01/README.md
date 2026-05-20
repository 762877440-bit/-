# TerminalAI - 智能终端助手

基于大语言模型的智能终端助手，支持聊天历史管理、长期记忆系统、网络搜索和工作流编排。

## 功能特性

- **聊天历史管理**：支持聊天记录的自动压缩和总结
- **长期记忆系统**：基于向量数据库的记忆存储与检索
- **网络搜索**：集成DuckDuckGo搜索引擎
- **工作流编排**：使用LangGraph构建Agent工作流
- **工具调用**：支持function call机制
- **异步流式输出**：支持实时响应

## 安装依赖

```bash
pip install pytest pytest-asyncio httpx duckduckgo_search langgraph pydantic python-dotenv PyYAML
```

## 配置说明

创建 `config.yaml` 文件：

```yaml
model:
  endpoint: "http://localhost:11434/api/generate"
  name: "qwen3.4-4b"
  temperature: 0.7
  max_tokens: 2048
  stream: true

memory:
  vector_db_path: "./chroma_db"

search:
  engine: "duckduckgo"
  timeout: 5
  max_results: 5

agent:
  verbose: false
  max_iterations: 5
```

也可以通过环境变量覆盖配置：
- `MODEL_ENDPOINT`: 模型API地址
- `MODEL_NAME`: 模型名称
- `SEARCH_ENGINE`: 搜索引擎

## 使用方法

### 运行主程序

```bash
python main.py
```

### 交互模式

```bash
python -c "
from model_client import ModelClient

client = ModelClient('http://localhost:11434/api/generate', 'qwen3.4-4b')
response = await client.generate([{'role': 'user', 'content': '你好'}])
print(response)
"
```

## 测试

运行所有测试：

```bash
python -m pytest tests/ -v
```

测试覆盖：
- 配置加载测试 (`test_config.py`)
- 模型客户端测试 (`test_model_client.py`)
- 记忆系统测试 (`test_memory_system.py`)
- 搜索工具测试 (`test_search_tool.py`)
- Agent工作流测试 (`test_agent_graph.py`)

## 项目结构

```
.
├── agent_graph.py          # LangGraph工作流定义
├── config.py              # 配置管理
├── config.yaml            # 配置文件
├── main.py                # 主程序入口
├── memory_system.py       # 记忆系统
├── model_client.py        # 模型客户端
├── search_tool.py         # 搜索工具
└── tests/
    ├── conftest.py        # 测试配置
    ├── test_agent_graph.py
    ├── test_config.py
    ├── test_memory_system.py
    ├── test_model_client.py
    └── test_search_tool.py
```

## License

MIT License