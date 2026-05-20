# tests/test_search_tool.py
import pytest
from unittest.mock import patch, MagicMock
from search_tool import SearchTool


@pytest.mark.asyncio
async def test_search_returns_results():
    """测试search正常返回结果列表"""
    mock_results = [
        {"title": "测试标题", "body": "测试摘要", "href": "http://example.com"}
    ]
    
    with patch("duckduckgo_search.DDGS") as mock_ddgs:
        mock_instance = MagicMock()
        mock_instance.text.return_value = mock_results
        mock_ddgs.return_value = mock_instance
        
        search_tool = SearchTool()
        results = await search_tool.search("测试查询")
        
        assert len(results) == 1
        assert results[0]["title"] == "测试标题"
        assert results[0]["snippet"] == "测试摘要"
        assert results[0]["url"] == "http://example.com"


@pytest.mark.asyncio
async def test_search_timeout():
    """测试搜索超时返回空列表"""
    with patch("duckduckgo_search.DDGS") as mock_ddgs:
        mock_instance = MagicMock()
        mock_instance.text.side_effect = Exception("Timeout")
        mock_ddgs.return_value = mock_instance
        
        search_tool = SearchTool(timeout=1)
        results = await search_tool.search("测试查询")
        
        assert results == []


@pytest.mark.asyncio
async def test_search_empty_results():
    """测试搜索返回空结果"""
    with patch("duckduckgo_search.DDGS") as mock_ddgs:
        mock_instance = MagicMock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value = mock_instance
        
        search_tool = SearchTool()
        results = await search_tool.search("无结果查询")
        
        assert results == []


def test_format_search_results():
    """测试格式化搜索结果"""
    search_tool = SearchTool()
    results = [
        {"title": "文章1", "snippet": "摘要内容1", "url": "http://a.com"},
        {"title": "文章2", "snippet": "摘要内容2", "url": "http://b.com"}
    ]
    
    formatted = search_tool.format_search_results_as_context(results)
    
    assert "[1] 文章1" in formatted
    assert "[2] 文章2" in formatted
    assert "来源:" in formatted


def test_format_empty_results():
    """测试格式化空搜索结果"""
    search_tool = SearchTool()
    formatted = search_tool.format_search_results_as_context([])
    
    assert formatted == "无搜索结果"