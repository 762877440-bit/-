# test_api.py
import httpx
import json

# 测试配置
config_model_name = "qwen/qwen3.5-4b"  # 配置文件中的模型名称
endpoint = "http://localhost:1234/v1/chat/completions"

print(f"配置的模型名称: '{config_model_name}'")
print(f"API端点: {endpoint}")

payload = {
    "model": config_model_name,
    "messages": [{"role": "user", "content": "你好"}],
    "temperature": 0.7,
    "max_tokens": 100,
    "stream": False
}

print(f"\n发送的请求数据: {json.dumps(payload, ensure_ascii=False)}")

try:
    response = httpx.post(endpoint, json=payload, timeout=10)
    print(f"\nHTTP状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容: {response.text}")
except Exception as e:
    print(f"\n请求失败: {type(e).__name__}: {str(e)}")