# API 设计文档 (API Specification)

## 1. 模块概览
| 模块 | 文件 | 职责 |
|------|------|------|
| 配置 | `config.py` | 加载环境变量、模型参数、路径 |
| 模型客户端 | `model_client.py` | 与 Qwen3.4-4b 的流式和非流式交互 |
| 记忆系统 | `memory_system.py` | 长期记忆的存取、检索、更新 |
| 搜索工具 | `search_tool.py` | 网页搜索 API 封装 |
| 工作流编排 | `agent_graph.py` | LangGraph 定义，包含节点和边 |
| 终端交互 | `cli.py` | 用户输入/输出、彩色打印、命令解析 |
| 主入口 | `main.py` | 组装并运行循环 |

## 2. 配置模块 (`config.py`)

```python
# 伪代码
class Config:
    model.endpoint: str          # 例如 "http://localhost:11434/api/generate"
    model.name: str              # "qwen3.4-4b"
    model.temperature: float     # 0.7
    model.max_tokens: int        # 2048
    model.stream: bool           # True
    
    memory.vector_db_path: str   # "./chroma_db"
    memory.mem0_config: dict     # Mem0 配置
    
    search.engine: str           # "duckduckgo" 或 "tavily"
    search.timeout: int          # 5 秒
    search.max_results: int      # 5
    
    agent.verbose: bool          # False，详细模式开关
    agent.max_iterations: int    # 5（最大工具调用轮次）

def load_config(path: str = "config.yaml") -> Config
    """从 YAML 文件加载配置，支持环境变量覆盖"""