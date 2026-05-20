# agent_graph.py
from typing import Dict, Any, List, Optional, AsyncGenerator
import json


class AgentState:
    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.memory_context: str = ""
        self.search_results: str = ""
        self.next_action: str = ""
        self.search_query: str = ""
        self.final_response: str = ""
        self.iteration: int = 0
        self.search_enabled: bool = True


class AgentGraph:
    def __init__(self, model_client, memory_system, search_tool, verbose=False, max_iterations=5):
        self.model_client = model_client
        self.memory_system = memory_system
        self.search_tool = search_tool
        self.verbose = verbose
        self.max_iterations = max_iterations

    def retrieve_memory(self, state: AgentState) -> AgentState:
        if state.messages:
            last_message = state.messages[-1]["content"]
            memories = self.memory_system.search_memory(last_message, top_k=3)
            if memories:
                memory_texts = [f"- {m['content']}" for m in memories]
                state.memory_context = "\n".join(memory_texts)
                if self.verbose:
                    print(f"[记忆检索] 找到 {len(memories)} 条相关记忆")
        return state

    def decide_action(self, state: AgentState) -> AgentState:
        if not state.messages:
            state.next_action = "respond"
            return state

        user_input = state.messages[-1]["content"].lower()
        search_triggers = ["天气", "新闻", "今天", "最新", "现在", "价格", "多少", "什么时间"]
        if state.search_enabled and any(trigger in user_input for trigger in search_triggers):
            state.next_action = "search"
            state.search_query = state.messages[-1]["content"]
        else:
            state.next_action = "respond"

        if self.verbose:
            print(f"[决策] 下一步动作: {state.next_action}")
            if state.next_action == "search":
                print(f"[决策] 搜索查询: {state.search_query}")
        return state

    async def execute_search(self, state: AgentState) -> AgentState:
        if state.search_query and state.search_enabled:
            if self.verbose:
                print(f"[搜索] 正在搜索: {state.search_query}")
            state.search_results = await self.search_tool.search_and_format(state.search_query)
            if self.verbose:
                print(f"[搜索] 结果: {state.search_results[:100]}...")
        return state

    async def generate_response_stream(self, state: AgentState) -> AsyncGenerator[str, None]:
        """流式生成最终响应，同时自动提取记忆"""
        context_parts = []
        if state.memory_context:
            context_parts.append(f"记忆信息:\n{state.memory_context}")
        if state.search_results and state.search_results != "无搜索结果":
            context_parts.append(f"搜索结果:\n{state.search_results}")

        system_prompt = f"""
你是一个专业的AI助手，使用中文回复。

{"\n\n".join(context_parts) if context_parts else "无额外上下文"}

请根据以上信息，用专业、客观、有条理的语气回答用户的问题。
如果使用了搜索结果，请在回答中注明信息来源。
"""
        messages = [{"role": "system", "content": system_prompt}] + state.messages

        full_response = ""
        async for token in self.model_client.generate_stream(messages):
            yield token
            full_response += token

        state.final_response = full_response
        self._extract_and_store_memory(state.messages)

    def _extract_and_store_memory(self, messages: List[Dict[str, str]]):
        if len(messages) >= 2:
            user_msg = messages[-1]["content"] if messages[-1]["role"] == "user" else ""
            memory_keywords = ["我是", "我叫", "我喜欢", "我的", "我来自", "我从事"]
            for keyword in memory_keywords:
                if keyword in user_msg:
                    sentences = user_msg.split("。")
                    for sentence in sentences:
                        if keyword in sentence:
                            self.memory_system.add_memory(sentence.strip())
                            if self.verbose:
                                print(f"[记忆] 存储: {sentence.strip()}")
                    break

    async def run_stream(self, user_input: str, search_enabled: bool = True) -> AsyncGenerator[str, None]:
        """流式运行Agent工作流，逐步产出最终响应的token"""
        state = AgentState()
        state.messages = [{"role": "user", "content": user_input}]
        state.search_enabled = search_enabled

        state = self.retrieve_memory(state)
        state = self.decide_action(state)

        if state.next_action == "search":
            state = await self.execute_search(state)

        async for token in self.generate_response_stream(state):
            yield token