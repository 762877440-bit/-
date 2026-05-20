# tests/test_model_client.py
import pytest
from unittest.mock import patch, MagicMock
from model_client import ModelClient, ModelConnectionError
import json


class MockAsyncContextManager:
    """模拟异步上下文管理器"""
    def __init__(self, return_value):
        self._return_value = return_value
    
    async def __aenter__(self):
        return self._return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
async def test_generate_stream_returns_tokens():
    """测试generate_stream返回有效token生成器"""
    mock_response = [
        '{"choices": [{"delta": {"content": "你"}}]}',
        '{"choices": [{"delta": {"content": "好"}}]}',
        '{"choices": [{"delta": {"content": "！"}}]}',
        '[DONE]'
    ]
    
    async def mock_stream():
        for chunk in mock_response:
            yield f"data: {chunk}"
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_stream_response = MagicMock()
        mock_stream_response.aiter_text = mock_stream
        mock_stream_response.status_code = 200
        
        # 创建异步上下文管理器用于stream
        mock_stream_context = MockAsyncContextManager(mock_stream_response)
        
        # 创建异步上下文管理器用于AsyncClient
        mock_client_context = MagicMock()
        mock_client_context.stream = MagicMock(return_value=mock_stream_context)
        mock_client.return_value = MockAsyncContextManager(mock_client_context)
        
        client = ModelClient("http://localhost:8080", "test-model")
        messages = [{"role": "user", "content": "你好"}]
        
        tokens = [token async for token in client.generate_stream(messages)]
        
        assert len(tokens) == 3
        assert "".join(tokens) == "你好！"


@pytest.mark.asyncio
async def test_generate_returns_full_string():
    """测试generate收集流式输出并返回完整字符串"""
    mock_response = [
        '{"choices": [{"delta": {"content": "测"}}]}',
        '{"choices": [{"delta": {"content": "试"}}]}',
        '[DONE]'
    ]
    
    async def mock_stream():
        for chunk in mock_response:
            yield f"data: {chunk}"
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_stream_response = MagicMock()
        mock_stream_response.aiter_text = mock_stream
        mock_stream_response.status_code = 200
        
        # 创建异步上下文管理器用于stream
        mock_stream_context = MockAsyncContextManager(mock_stream_response)
        
        # 创建异步上下文管理器用于AsyncClient
        mock_client_context = MagicMock()
        mock_client_context.stream = MagicMock(return_value=mock_stream_context)
        mock_client.return_value = MockAsyncContextManager(mock_client_context)
        
        client = ModelClient("http://localhost:8080", "test-model")
        messages = [{"role": "user", "content": "测试"}]
        
        result = await client.generate(messages)
        
        assert result == "测试"


@pytest.mark.asyncio
async def test_network_error_raises_exception():
    """测试网络错误时抛出自定义异常"""
    with patch("httpx.AsyncClient") as mock_client:
        # 创建会抛出异常的异步上下文管理器
        async def mock_aenter():
            raise Exception("Connection refused")
        
        mock_context = MagicMock()
        mock_context.__aenter__ = mock_aenter
        mock_client.return_value = mock_context
        
        client = ModelClient("http://localhost:8080", "test-model")
        messages = [{"role": "user", "content": "测试"}]
        
        with pytest.raises(ModelConnectionError):
            async for _ in client.generate_stream(messages):
                pass


@pytest.mark.asyncio
async def test_generate_with_tools():
    """测试传递tools参数时消息格式正确"""
    tools = [{
        "type": "function",
        "function": {
            "name": "search",
            "description": "搜索",
            "parameters": {"query": {"type": "string"}}
        }
    }]
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "工具调用响应"}}]
        }
        
        # 创建异步上下文管理器用于AsyncClient
        mock_client_context = MagicMock()
        # post方法需要返回一个协程
        async def mock_post(*args, **kwargs):
            return mock_response
        mock_client_context.post = mock_post
        
        mock_client_context_mgr = MockAsyncContextManager(mock_client_context)
        mock_client.return_value = mock_client_context_mgr
        
        client = ModelClient("http://localhost:8080", "test-model")
        messages = [{"role": "user", "content": "测试工具调用"}]
        
        result = await client.generate_with_tools(messages, tools)
        
        assert "choices" in result