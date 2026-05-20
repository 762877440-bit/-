# tests/test_agent_graph.py
import pytest
from unittest.mock import MagicMock
from agent_graph import AgentGraph, AgentState


@pytest.mark.asyncio
async def test_retrieve_memory_node():
    """测试retrieve_memory节点"""
    # 创建mock组件
    async def mock_generate(*args, **kwargs):
        return "模拟回复"
    
    mock_model = MagicMock()
    mock_model.generate = mock_generate
    
    mock_memory = MagicMock()
    mock_search = MagicMock()
    
    # 设置mock返回值
    async def mock_search_and_format(*args, **kwargs):
        return "搜索结果"
    
    mock_search.search_and_format = mock_search_and_format
    mock_memory.search_memory.return_value = [
        {"content": "我叫张三"}
    ]
    
    agent = AgentGraph(mock_model, mock_memory, mock_search, verbose=True)
    
    # 创建状态
    state = AgentState()
    state.messages = [{"role": "user", "content": "我叫什么"}]
    
    # 执行节点
    result = agent.retrieve_memory(state)
    
    # 验证
    assert "我叫张三" in result.memory_context
    mock_memory.search_memory.assert_called_once_with("我叫什么")


@pytest.mark.asyncio
async def test_decide_action_search():
    """测试decide_action节点决定搜索"""
    async def mock_generate(*args, **kwargs):
        return "模拟回复"
    
    mock_model = MagicMock()
    mock_model.generate = mock_generate
    
    mock_memory = MagicMock()
    mock_search = MagicMock()
    
    async def mock_search_and_format(*args, **kwargs):
        return "搜索结果"
    
    mock_search.search_and_format = mock_search_and_format
    
    agent = AgentGraph(mock_model, mock_memory, mock_search, verbose=True)
    
    state = AgentState()
    state.messages = [{"role": "user", "content": "今天天气怎么样"}]
    state.search_enabled = True
    
    result = agent.decide_action(state)
    
    assert result.next_action == "search"
    assert result.search_query == "今天天气怎么样"


@pytest.mark.asyncio
async def test_decide_action_respond():
    """测试decide_action节点决定直接响应"""
    async def mock_generate(*args, **kwargs):
        return "模拟回复"
    
    mock_model = MagicMock()
    mock_model.generate = mock_generate
    
    mock_memory = MagicMock()
    mock_search = MagicMock()
    
    async def mock_search_and_format(*args, **kwargs):
        return "搜索结果"
    
    mock_search.search_and_format = mock_search_and_format
    
    agent = AgentGraph(mock_model, mock_memory, mock_search, verbose=True)
    
    state = AgentState()
    state.messages = [{"role": "user", "content": "你好"}]
    state.search_enabled = True
    
    result = agent.decide_action(state)
    
    assert result.next_action == "respond"


@pytest.mark.asyncio
async def test_execute_search_node():
    """测试execute_search节点"""
    async def mock_generate(*args, **kwargs):
        return "模拟回复"
    
    mock_model = MagicMock()
    mock_model.generate = mock_generate
    
    mock_memory = MagicMock()
    mock_search = MagicMock()
    
    async def mock_search_and_format(*args, **kwargs):
        return "搜索结果内容"
    
    mock_search.search_and_format = mock_search_and_format
    
    agent = AgentGraph(mock_model, mock_memory, mock_search, verbose=True)
    
    state = AgentState()
    state.search_query = "测试搜索"
    state.search_enabled = True
    
    result = await agent.execute_search(state)
    
    assert result.search_results == "搜索结果内容"


@pytest.mark.asyncio
async def test_execute_search_disabled():
    """测试搜索功能关闭时不执行搜索"""
    async def mock_generate(*args, **kwargs):
        return "模拟回复"
    
    mock_model = MagicMock()
    mock_model.generate = mock_generate
    
    mock_memory = MagicMock()
    mock_search = MagicMock()
    
    async def mock_search_and_format(*args, **kwargs):
        return "搜索结果"
    
    mock_search.search_and_format = mock_search_and_format
    
    agent = AgentGraph(mock_model, mock_memory, mock_search, verbose=True)
    
    state = AgentState()
    state.search_query = "测试搜索"
    state.search_enabled = False
    
    result = await agent.execute_search(state)
    
    assert result.search_results == ""


@pytest.mark.asyncio
async def test_generate_response_node():
    """测试generate_response节点"""
    async def mock_generate(*args, **kwargs):
        return "这是回复内容"
    
    mock_model = MagicMock()
    mock_model.generate = mock_generate
    
    mock_memory = MagicMock()
    mock_search = MagicMock()
    
    async def mock_search_and_format(*args, **kwargs):
        return "搜索结果"
    
    mock_search.search_and_format = mock_search_and_format
    
    agent = AgentGraph(mock_model, mock_memory, mock_search, verbose=True)
    
    state = AgentState()
    state.messages = [{"role": "user", "content": "你好"}]
    state.memory_context = ""
    state.search_results = ""
    
    result = await agent.generate_response(state)
    
    assert result.final_response == "这是回复内容"


def test_should_search_returns_correct_route():
    """测试条件边路由"""
    async def mock_generate(*args, **kwargs):
        return "模拟回复"
    
    mock_model = MagicMock()
    mock_model.generate = mock_generate
    
    mock_memory = MagicMock()
    mock_search = MagicMock()
    
    async def mock_search_and_format(*args, **kwargs):
        return "搜索结果"
    
    mock_search.search_and_format = mock_search_and_format
    
    agent = AgentGraph(mock_model, mock_memory, mock_search)
    
    state_search = AgentState()
    state_search.next_action = "search"
    assert agent._should_search(state_search) == "search"
    
    state_respond = AgentState()
    state_respond.next_action = "respond"
    assert agent._should_search(state_respond) == "respond"