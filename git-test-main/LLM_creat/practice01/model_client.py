# model_client.py
import asyncio
import json
import httpx
from typing import AsyncGenerator, Optional, List, Dict, Any


class ModelConnectionError(Exception):
    pass


class ModelClient:
    def __init__(self, endpoint: str, model_name: str, temperature: float = 0.7, max_tokens: int = 2048):
        self.endpoint = endpoint
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def generate_stream(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict]] = None) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True
        }
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", self.endpoint, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise ModelConnectionError(f"HTTP {response.status_code}: {error_text.decode()}")
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or line.startswith(":"):
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                # 兼容 OpenAI / LM Studio 格式
                                if "choices" in data and len(data["choices"]) > 0:
                                    choice = data["choices"][0]
                                    delta = choice.get("delta", {})
                                    if "content" in delta and delta["content"]:
                                        yield delta["content"]
                                    # 兼容非流式message格式
                                    elif "message" in choice and choice["message"].get("content"):
                                        yield choice["message"]["content"]
                            except json.JSONDecodeError:
                                continue
        except httpx.HTTPError as e:
            raise ModelConnectionError(f"HTTP连接错误: {str(e)}")
        except Exception as e:
            raise ModelConnectionError(f"模型调用失败: {str(e)}")

    async def generate(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict]] = None) -> str:
        full = ""
        async for token in self.generate_stream(messages, tools):
            full += token
        return full