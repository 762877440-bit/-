# main.py
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import load_config
from model_client import ModelClient
from memory_system import MemorySystem
from search_tool import SearchTool
from agent_graph import AgentGraph
from cli import CLI


def main():
    config = load_config()
    

    # 使用 config 中的模型名称（已从 config.yaml 读取 "qwen/qwen3.5-4b"）
    model_client = ModelClient(
        endpoint=config.model.endpoint,
        model_name=config.model.name,   # 关键：不要硬编码！
        temperature=config.model.temperature,
        max_tokens=config.model.max_tokens
    )

    memory_system = MemorySystem(storage_path=config.memory.vector_db_path)
    search_tool = SearchTool(
        engine=config.search.engine,
        timeout=config.search.timeout,
        max_results=config.search.max_results
    )

    agent = AgentGraph(
        model_client=model_client,
        memory_system=memory_system,
        search_tool=search_tool,
        verbose=config.agent.verbose,
        max_iterations=config.agent.max_iterations
    )

    cli = CLI(agent=agent, model_client=model_client)
    asyncio.run(cli.chat_loop())   # 注意使用 chat_loop，不是 stream_chat_loop


if __name__ == "__main__":
    main()