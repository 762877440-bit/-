# practice04/anythingllm_tools.py
import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")
ANYTHINGLLM_WORKSPACE_SLUG = os.getenv("ANYTHINGLLM_WORKSPACE_SLUG")
ANYTHINGLLM_BASE_URL = os.getenv("ANYTHINGLLM_BASE_URL", "http://localhost:3001")

workspace_slug = ANYTHINGLLM_WORKSPACE_SLUG or "mywork"
ANYTHING_API_URL = f"{ANYTHINGLLM_BASE_URL}/api/v1/workspace/{workspace_slug}/chat"

def anythingllm_query(message: str) -> Dict[str, Any]:
    if not ANYTHINGLLM_API_KEY:
        return {"success": False, "error": "未配置 ANYTHINGLLM_API_KEY 环境变量"}

    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"message": message}

    try:
        # 设置超时时间为 120 秒（本地模型可能较慢）
        response = requests.post(ANYTHING_API_URL, json=payload, headers=headers, timeout=120)
        response.raise_for_status()  # 如果状态码不是 200，会抛出异常

        response_json = response.json()
        # 提取回答字段（兼容 textResponse 和 text）
        answer = response_json.get("textResponse") or response_json.get("text") or ""

        if not answer:
            # 如果回答为空，检查是否有错误
            error_msg = response_json.get("error")
            if error_msg:
                return {"success": False, "error": f"AnythingLLM 错误: {error_msg}"}
            else:
                return {"success": False, "error": "AnythingLLM 返回空内容"}

        return {"success": True, "content": answer, "raw": response_json}

    except requests.exceptions.Timeout:
        return {"success": False, "error": f"请求超时（{120}秒），AnythingLLM 响应太慢，请检查模型是否已加载"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"网络请求失败: {str(e)}"}
    except json.JSONDecodeError:
        return {"success": False, "error": "响应解析失败，非 JSON 格式"}
    except Exception as e:
        return {"success": False, "error": str(e)}