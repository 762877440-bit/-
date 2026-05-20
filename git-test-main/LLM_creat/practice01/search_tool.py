# search_tool.py
import asyncio
from typing import List, Dict, Any, Optional
import httpx


class SearchTool:
    def __init__(self, engine: str = "duckduckgo", timeout: int = 5, max_results: int = 5):
        self.engine = engine
        self.timeout = timeout
        self.max_results = max_results

    async def search(self, query: str) -> List[Dict[str, str]]:
        try:
            results = await asyncio.wait_for(
                self._perform_search(query),
                timeout=self.timeout
            )
            return results
        except asyncio.TimeoutError:
            return []
        except Exception:
            return []

    async def _perform_search(self, query: str) -> List[Dict[str, str]]:
        if self.engine == "duckduckgo":
            # 使用 DuckDuckGo HTML API (免费，无需 key)
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    # 从 RelatedTopics 提取结果
                    for topic in data.get("RelatedTopics", []):
                        if isinstance(topic, dict) and "Text" in topic and "FirstURL" in topic:
                            results.append({
                                "title": topic["Text"].split(" - ")[0] if " - " in topic["Text"] else topic["Text"],
                                "snippet": topic["Text"],
                                "url": topic["FirstURL"]
                            })
                        elif isinstance(topic, dict) and "Topics" in topic:
                            for subtopic in topic["Topics"]:
                                if "Text" in subtopic and "FirstURL" in subtopic:
                                    results.append({
                                        "title": subtopic["Text"].split(" - ")[0],
                                        "snippet": subtopic["Text"],
                                        "url": subtopic["FirstURL"]
                                    })
                        if len(results) >= self.max_results:
                            break
                    return results[:self.max_results]
        return []

    def format_search_results_as_context(self, results: List[Dict[str, str]]) -> str:
        if not results:
            return "无搜索结果"

        parts = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "无标题")
            snippet = r.get("snippet", "")
            url = r.get("url", "")
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            parts.append(f"[{i}] {title}\n{snippet}\n来源: {url}\n")
        return "\n".join(parts)

    async def search_and_format(self, query: str) -> str:
        results = await self.search(query)
        return self.format_search_results_as_context(results)