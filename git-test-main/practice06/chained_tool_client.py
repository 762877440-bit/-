#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chained_tool_client.py
链式工具调用（Chained Tool Calls）交互式客户端
基于 practice06/tool_client.py 实现，支持：
- 文件搜索、读取、写入
- 网页获取
- LLM 自主决策下一步调用哪个工具
- 中间结果自动记录并在后续调用中引用
"""

import os
import sys
import json
import re
import http.client
import ssl
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional

# ==================== 环境配置与 LLM 调用（源自 tool_client.py） ====================

def load_env():
    """加载 .env 文件中的配置（假设文件位于项目根目录）"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if not os.path.exists(env_path):
        env_path = '.env'
    if not os.path.exists(env_path):
        print(f"警告：未找到 .env 文件，将使用默认配置。请确保已设置 BASE_URL, MODEL, API_KEY 等环境变量。")
        return
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value

def call_llm(messages, tools=None):
    """
    调用 LLM API（非流式），支持工具调用。
    返回 OpenAI 风格的响应字典，或 None。
    """
    base_url = os.getenv('BASE_URL')
    model = os.getenv('MODEL')
    api_key = os.getenv('API_KEY')
    if not all([base_url, model, api_key]):
        print("错误：缺少 LLM 配置，请设置 BASE_URL, MODEL, API_KEY")
        return None

    parsed_url = urlparse(base_url)
    host = parsed_url.netloc
    path = parsed_url.path.rstrip('/') + '/chat/completions'
    protocol = parsed_url.scheme

    data = {
        "model": model,
        "messages": messages,
        "temperature": float(os.getenv('TEMPERATURE', '0.3')),  # 降低温度以获得更确定的决策
        "max_tokens": int(os.getenv('MAX_TOKENS', '4096'))
    }
    if tools:
        data["tools"] = tools
        data["tool_choice"] = "auto"

    if protocol == 'https':
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        conn = http.client.HTTPSConnection(host, context=context)
    else:
        conn = http.client.HTTPConnection(host)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    try:
        conn.request('POST', path, json.dumps(data), headers)
        response = conn.getresponse()
        response_content = response.read().decode()
        try:
            response_data = json.loads(response_content)
        except json.JSONDecodeError:
            if response.status == 200:
                return {"choices": [{"message": {"content": response_content}}]}
            else:
                print(f"API 错误: {response_content}")
                return None
        if response.status == 200:
            return response_data
        else:
            error_info = response_data.get('error', {})
            print(f"API 错误: {error_info.get('message', '未知错误')}")
            return None
    finally:
        conn.close()

# ==================== 可用工具定义（适配链式调用） ====================

def search_files(directory: str, keyword: str) -> str:
    """
    在指定目录（递归）下搜索所有包含关键词 keyword 的文件，返回文件路径列表的 JSON。
    """
    if not os.path.isdir(directory):
        return json.dumps({"status": "error", "message": f"目录不存在: {directory}"})
    matched = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if keyword in content:
                        matched.append(file_path)
            except Exception:
                continue
    return json.dumps({"status": "success", "files": matched, "count": len(matched)})

def read_file(file_path: str) -> str:
    """
    读取指定路径的文件内容，返回包含 content 的 JSON。
    """
    if not os.path.isfile(file_path):
        return json.dumps({"status": "error", "message": f"文件不存在: {file_path}"})
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return json.dumps({"status": "success", "content": content, "path": file_path})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def write_file(file_path: str, content: str) -> str:
    """
    将内容写入文件（覆盖模式）。若目录不存在则自动创建。
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"status": "success", "message": f"文件已写入: {file_path}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def fetch_webpage(url: str) -> str:
    """
    访问指定 URL 并返回网页文本内容（自动处理编码，限制长度）。
    """
    url = url.strip('`')
    try:
        parsed = urlparse(url)
        host = parsed.netloc
        from urllib.parse import quote
        path = parsed.path if parsed.path else '/'
        path = quote(path, safe='/')
        if parsed.query:
            path += '?' + parsed.query
        protocol = parsed.scheme

        if protocol == 'https':
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            conn = http.client.HTTPSConnection(host, context=context)
        else:
            conn = http.client.HTTPConnection(host)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        conn.request('GET', path, headers=headers)
        response = conn.getresponse()
        content = response.read().decode('utf-8', errors='replace')
        max_len = 100000
        if len(content) > max_len:
            content = content[:max_len] + "\n... (内容已截断)"
        return json.dumps({"status": "success", "data": content})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# ==================== 链式调用核心组件 ====================

class ChainedCallContext:
    """
    链式调用上下文管理器。
    记录每一步的工具调用和结果，存储中间变量，并防止无限循环。
    """
    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self.history: List[Dict[str, Any]] = []
        self.variables: Dict[str, Any] = {}
        self.current_iteration = 0

    def add_step(self, tool_name: str, arguments: Dict, result: Any):
        self.current_iteration += 1
        step = {
            "iteration": self.current_iteration,
            "tool": tool_name,
            "arguments": arguments,
            "result": result
        }
        self.history.append(step)
        var_key = f"{tool_name}_out_{self.current_iteration}"
        self.variables[var_key] = result

    def get_history_summary(self) -> str:
        if not self.history:
            return "尚未执行任何工具。"
        lines = []
        for step in self.history:
            result_preview = str(step['result'])[:300]
            lines.append(
                f"步骤{step['iteration']}: 调用 {step['tool']}, "
                f"参数: {json.dumps(step['arguments'], ensure_ascii=False)}, "
                f"结果预览: {result_preview}"
            )
        return "\n".join(lines)

    def is_limit_reached(self) -> bool:
        return self.current_iteration >= self.max_iterations

def build_analysis_prompt(user_request: str, context: ChainedCallContext) -> str:
    vars_display = json.dumps(context.variables, ensure_ascii=False, indent=2)
    prompt = f"""
## 用户原始请求
{user_request}

## 已执行的工具调用历史
{context.get_history_summary()}

## 当前可用中间变量
{vars_display}

## 可用工具列表（函数签名）
1. search_files(directory, keyword)  
   在目录中搜索包含关键词的文件，返回文件路径列表。
2. read_file(file_path)  
   读取指定文件的内容，返回文件文本。
3. write_file(file_path, content)  
   将内容写入指定文件。
4. fetch_webpage(url)  
   获取网页的文本内容。

## 决策规则
- 如果根据已有信息已经可以给出用户请求的最终答案，请输出 `"done": true` 并提供 `"answer"` 字段。
- 如果还需要继续调用工具才能得到答案，请输出 `"done": false` 并指定下一个要调用的工具（`tool_call` 对象）。
- 工具参数应尽可能使用历史结果或中间变量中的具体值。例如上一步返回的文件列表，可以直接填入 `file_path` 参数。
- 每次只能调用一个工具。完成一个工具后，系统会将结果存入上下文，然后再次询问你。
- 避免重复调用相同的工具（除非有必要）。

## 输出格式要求（仅输出 JSON，不要有任何额外文本）
### 情况一：任务已完成
{{"done": true, "answer": "最终回答内容"}}

### 情况二：需要继续调用工具
{{"done": false, "tool_call": {{"name": "工具名称", "arguments": {{"参数名1": "参数值1", "参数名2": "参数值2"}}}}}}

现在请根据以上信息作出决策：
"""
    return prompt

def execute_chained_tool_call(user_request: str, max_iterations: int = 5) -> str:
    """
    执行链式工具调用的主循环。
    返回最终答案（字符串）。
    """
    context = ChainedCallContext(max_iterations=max_iterations)

    while not context.is_limit_reached():
        prompt = build_analysis_prompt(user_request, context)
        messages = [
            {"role": "system", "content": "你是一个智能工具调度助手。你必须严格按 JSON 格式输出决策，不要有任何额外解释。"},
            {"role": "user", "content": prompt}
        ]
        response = call_llm(messages, tools=None)
        if not response:
            print("LLM 调用失败")
            return "错误：无法获取 LLM 决策"

        try:
            assistant_content = response['choices'][0]['message']['content']
        except (KeyError, IndexError):
            print("LLM 返回格式错误")
            return "错误：LLM 返回格式异常"

        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', assistant_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', assistant_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                else:
                    raise ValueError("未找到 JSON 对象")
            decision = json.loads(json_str)
        except Exception as e:
            print(f"解析 LLM 输出失败: {e}\n原始内容: {assistant_content}")
            context.add_step("__parse_error__", {}, f"JSON 解析失败: {assistant_content[:200]}")
            continue

        if decision.get("done"):
            answer = decision.get("answer", "任务完成，但未提供具体答案。")
            print(f"\n[链式调用完成] 最终答案: {answer}")
            return answer

        tool_call = decision.get("tool_call")
        if not tool_call:
            print("决策中缺少 tool_call 字段")
            context.add_step("__invalid_decision__", {}, "缺少 tool_call")
            continue

        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})

        tool_func = globals().get(tool_name)
        if not tool_func:
            error_msg = f"未知工具: {tool_name}"
            print(error_msg)
            context.add_step(tool_name, arguments, error_msg)
            continue

        try:
            result = tool_func(**arguments)
        except Exception as e:
            result = f"工具执行异常: {str(e)}"

        context.add_step(tool_name, arguments, result)
        print(f"[步骤{context.current_iteration}] 调用 {tool_name}({arguments}) -> {str(result)[:150]}")

    return "达到最大迭代次数，任务未完成。"

# ==================== 交互式主程序 ====================

def main():
    load_env()
    print("=" * 60)
    print("链式工具调用客户端 (Chained Tool Calls)")
    print("输入您的问题，我会根据需要自动调用工具（搜索文件、读写文件、获取网页等）")
    print("输入 'exit' 或 'quit' 退出程序")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n>>> 你: ").strip()
            if user_input.lower() in ['exit', 'quit', '退出']:
                print("再见！")
                break
            if not user_input:
                continue

            print("\n[系统] 开始链式调用分析...")
            answer = execute_chained_tool_call(user_input, max_iterations=6)
            print(f"\n[助手] {answer}")

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    main()