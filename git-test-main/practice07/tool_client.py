import os
import sys
import json
import re
import http.client
import ssl
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional, Tuple

from anythingllm_tools import anythingllm_query


def load_env():
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
        "temperature": float(os.getenv('TEMPERATURE', '0.3')),
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


def stream_llm(messages):
    base_url = os.getenv('BASE_URL')
    model = os.getenv('MODEL')
    api_key = os.getenv('API_KEY')
    if not all([base_url, model, api_key]):
        print("错误：缺少 LLM 配置")
        return None

    parsed_url = urlparse(base_url)
    host = parsed_url.netloc
    path = parsed_url.path.rstrip('/') + '/chat/completions'
    protocol = parsed_url.scheme

    data = {
        "model": model,
        "messages": messages,
        "temperature": float(os.getenv('TEMPERATURE', '0.7')),
        "max_tokens": int(os.getenv('MAX_TOKENS', '4096')),
        "stream": True
    }

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
        if response.status != 200:
            error_data = json.loads(response.read().decode())
            print(f"API错误: {error_data.get('error', {}).get('message', '未知错误')}")
            return None
        full_response = ""
        for line in response:
            line = line.decode().strip()
            if not line:
                continue
            if line.startswith('data: '):
                line = line[6:]
                if line == '[DONE]':
                    break
                try:
                    chunk = json.loads(line)
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        if 'content' in delta:
                            content = delta['content']
                            print(content, end='', flush=True)
                            full_response += content
                except json.JSONDecodeError:
                    pass
        print()
        return full_response
    finally:
        conn.close()


def search_files(directory: str, keyword: str) -> str:
    if not os.path.isdir(directory):
        return json.dumps({"status": "error", "message": f"目录不存在: {directory}"}, ensure_ascii=False)
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
    return json.dumps({"status": "success", "files": matched, "count": len(matched)}, ensure_ascii=False)


def read_file(file_path: str) -> str:
    if not os.path.isfile(file_path):
        return json.dumps({"status": "error", "message": f"文件不存在: {file_path}"}, ensure_ascii=False)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return json.dumps({"status": "success", "content": content, "path": file_path}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


def write_file(file_path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"status": "success", "message": f"文件已写入: {file_path}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


def fetch_webpage(url: str) -> str:
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
        return json.dumps({"status": "success", "data": content}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


def query_anythingllm_tool(question: str) -> str:
    res = anythingllm_query(question)
    if res.get("success"):
        return json.dumps({"status": "success", "data": res.get("content", "")}, ensure_ascii=False)
    else:
        return json.dumps({"status": "error", "message": res.get("error", "未知错误")}, ensure_ascii=False)


# ==================== 可用工具定义（OpenAI Function Calling 格式） ====================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "在指定目录下递归搜索包含指定关键词的文件，返回文件路径列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "要搜索的目录路径"},
                    "keyword": {"type": "string", "description": "要搜索的关键词"}
                },
                "required": ["directory", "keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定文件的内容，返回文件文本",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件的完整路径"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "将内容写入指定文件（覆盖模式），目录不存在时自动创建",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "要写入的文件路径"},
                    "content": {"type": "string", "description": "要写入的内容"}
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "description": "访问指定URL并返回网页文本内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "网页URL地址"}
                },
                "required": ["url"]
            }
        }
    },
]

TOOL_FUNCTION_MAP = {
    "search_files": search_files,
    "read_file": read_file,
    "write_file": write_file,
    "fetch_webpage": fetch_webpage,
}

# ==================== ChainedCallContext 链式调用上下文管理器 ====================

class ChainedCallContext:
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
        var_key = f"step_{self.current_iteration}_{tool_name}_result"
        self.variables[var_key] = result

    def get_history_summary(self) -> str:
        if not self.history:
            return "（尚无已执行的工具调用）"
        lines = []
        for step in self.history:
            result_preview = str(step['result'])[:500]
            lines.append(
                f"--- 步骤 {step['iteration']} ---\n"
                f"  工具名: {step['tool']}\n"
                f"  参数: {json.dumps(step['arguments'], ensure_ascii=False)}\n"
                f"  结果预览: {result_preview}"
            )
        return "\n".join(lines)

    def get_variables_summary(self) -> str:
        if not self.variables:
            return "（尚无可用中间变量）"
        lines = []
        for key, value in self.variables.items():
            preview = str(value)[:200]
            lines.append(f"  {key}: {preview}")
        return "\n".join(lines)

    def is_limit_reached(self) -> bool:
        return self.current_iteration >= self.max_iterations


# ==================== build_analysis_prompt 分析提示词构建函数 ====================

def build_analysis_prompt(user_request: str, context: ChainedCallContext) -> str:
    prompt = f"""## 用户原始请求
{user_request}

## 已执行的工具调用历史
{context.get_history_summary()}

## 中间变量（可供后续步骤引用）
{context.get_variables_summary()}

## 可用工具
1. search_files(directory, keyword) — 在目录中搜索包含关键词的文件，返回文件路径列表
2. read_file(file_path) — 读取指定文件的内容
3. write_file(file_path, content) — 将内容写入指定文件
4. fetch_webpage(url) — 获取网页文本内容

## 决策规则
- 如果根据已有信息可以完成用户请求，选择"任务完成"
- 如果还需调用工具，选择"继续调用工具"，参数优先使用历史结果中的具体值
- 每次只能调用一个工具，完成后系统会将结果存入上下文供下次决策
- 避免无意义的重复调用

## 输出格式（仅输出 JSON，不要额外文本）
### 任务完成时：
{{"done": true, "answer": "最终回答"}}
### 继续调用工具时：
{{"done": false, "tool_call": {{"name": "工具名", "arguments": {{"参数名": "参数值"}}}}}}

请决定下一步："""
    return prompt


# ==================== parse_llm_decision 解析 LLM 响应 ====================

def parse_llm_decision(response: dict) -> Tuple[Optional[dict], str]:
    if response is None:
        return None, "错误：LLM 响应为 None"

    try:
        choice = response.get('choices', [{}])[0]
        message = choice.get('message', {})
    except (KeyError, IndexError, TypeError):
        return None, "错误：LLM 返回格式异常，缺少 choices"

    # 方式一：检查 tool_calls 格式（OpenAI 标准 Function Calling）
    tool_calls = message.get('tool_calls')
    if tool_calls and len(tool_calls) > 0:
        tool_call = tool_calls[0]
        function_info = tool_call.get('function', {})
        tool_name = function_info.get('name', '')
        arguments_str = function_info.get('arguments', '{}')
        if isinstance(arguments_str, str):
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError:
                arguments = {}
        else:
            arguments = arguments_str
        decision = {
            "done": False,
            "tool_call": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        print(f"[解析] 使用 tool_calls 格式: {tool_name}")
        return decision, "tool_calls"

    # 方式二：检查 content 中的 JSON 格式
    assistant_content = message.get('content', '')
    if not assistant_content:
        return None, "错误：LLM 返回空内容"

    json_str = _extract_json_from_text(assistant_content)
    if json_str is None:
        return None, f"错误：无法从 LLM 响应中提取 JSON\n原始内容: {assistant_content[:500]}"

    try:
        decision = json.loads(json_str)
        print(f"[解析] 使用 JSON content 格式")
        return decision, "json_content"
    except json.JSONDecodeError as e:
        return None, f"错误：JSON 解析失败: {e}\n提取的 JSON 字符串: {json_str[:300]}"


def _extract_json_from_text(text: str) -> Optional[str]:
    if not text:
        return None

    # 尝试提取 ```json ... ``` 代码块
    json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_block_match:
        return json_block_match.group(1)

    # 尝试提取 ``` ... ``` 代码块（无语言标记）
    code_block_match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1)

    # 尝试匹配最外层的大括号 JSON 对象
    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        return brace_match.group()

    return None


# ==================== build_chained_system_prompt 构建链式调用 system prompt ====================

def build_chained_system_prompt() -> str:
    return """你是一个智能工具调度助手，负责通过链式工具调用来完成用户的复杂请求。

## 链式调用规则
1. **顺序依赖**：工具的调用顺序很重要。例如，必须先搜索文件(search_files)获取文件列表，才能读取文件(read_file)；必须先读取文件获取数据，才能写入新文件(write_file)。
2. **中间结果利用**：每一步工具调用的结果会作为中间变量存储在上下文中。后续步骤应直接使用这些中间结果中的信息（如文件路径、文件内容等），而不是重复查询。
3. **单步执行**：每次决策只能选择调用一个工具。系统执行完该工具后会将结果存入上下文，然后再次询问你下一步操作。
4. **任务终止**：当已有信息足够回答用户请求时，必须设置 done=true 并给出最终答案。
5. **避免冗余**：不要重复调用相同参数的工具，除非确有必要。

## 链式调用示例
**场景1：文件搜索链式调用**
- 用户请求："查找包含关键词'def'的文件并总结内容"
- 步骤1: search_files(directory="practice06", keyword="def") → 返回文件列表
- 步骤2: read_file(file_path="practice06/xxx.py") → 读取第1个文件
- 步骤3: read_file(file_path="practice06/yyy.py") → 读取第2个文件
- 最终: done=true, answer="总结内容..."

**场景2：多文件数值运算**
- 用户请求："读取A.txt和B.txt中的数字，计算和并写入result.txt"
- 步骤1: read_file(file_path="A.txt") → 返回内容"42"
- 步骤2: read_file(file_path="B.txt") → 返回内容"58"
- 步骤3: write_file(file_path="result.txt", content="100") → 写入成功
- 最终: done=true, answer="已将结果100写入result.txt"

**场景3：网页内容处理**
- 用户请求："访问某网页并保存内容摘要"
- 步骤1: fetch_webpage(url="...") → 返回HTML内容
- 步骤2: 根据网页内容决定下一步操作（如 write_file 保存摘要）

## 上下文变量使用
每步工具调用后，结果会保存在变量中，格式为：
  step_{N}_{工具名}_result
例如 step_1_search_files_result 保存了第一次搜索的结果。

## 输出要求
你必须严格按照以下 JSON 格式输出（不要输出任何额外文本或解释）：
- 需要调用工具: {"done": false, "tool_call": {"name": "工具名", "arguments": {"参数": "值"}}}
- 任务已完成: {"done": true, "answer": "最终回答内容"}"""


# ==================== execute_chained_tool_call 链式调用执行函数 ====================

def execute_chained_tool_call(user_request: str, max_iterations: int = 10) -> str:
    context = ChainedCallContext(max_iterations=max_iterations)

    system_prompt = build_chained_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
    ]

    while not context.is_limit_reached():
        analysis_prompt = build_analysis_prompt(user_request, context)
        messages.append({"role": "user", "content": analysis_prompt})

        response = call_llm(messages, tools=TOOLS)
        if response is None:
            error_msg = "错误：LLM 调用返回 None"
            print(error_msg)
            return error_msg

        decision, parse_mode = parse_llm_decision(response)
        if decision is None:
            print(f"[警告] {parse_mode}")
            context.add_step("__parse_error__", {}, parse_mode)
            messages.pop()
            continue

        if decision.get("done"):
            answer = decision.get("answer", "任务完成")
            print(f"\n[链式调用完成] 总共执行 {context.current_iteration} 步")
            print(f"[最终答案] {answer}")
            return answer

        tool_call = decision.get("tool_call")
        if not tool_call:
            print("[警告] 决策中缺少 tool_call，但 done 不为 true")
            context.add_step("__invalid_decision__", {}, "缺少 tool_call 字段")
            messages.pop()
            continue

        tool_name = tool_call.get("name", "")
        arguments = tool_call.get("arguments", {})

        tool_func = TOOL_FUNCTION_MAP.get(tool_name)
        if not tool_func:
            error_msg = f"未知工具: {tool_name}"
            print(f"[错误] {error_msg}")
            context.add_step(tool_name, arguments, error_msg)
            messages.pop()
            continue

        try:
            result = tool_func(**arguments)
        except Exception as e:
            result = json.dumps({"status": "error", "message": f"工具执行异常: {str(e)}"}, ensure_ascii=False)
            print(f"[异常] 工具 {tool_name} 执行出错: {e}")

        context.add_step(tool_name, arguments, result)
        print(f"[步骤 {context.current_iteration}] {tool_name}({json.dumps(arguments, ensure_ascii=False)})")
        print(f"  结果: {str(result)[:200]}")

        messages.append({"role": "assistant", "content": json.dumps({"tool_call": tool_name, "arguments": arguments}, ensure_ascii=False)})
        messages.append({"role": "tool", "content": str(result)})

        messages.pop()

    print(f"\n[链式调用终止] 达到最大迭代次数 {max_iterations}，任务未完成")
    return f"达到最大迭代次数（{max_iterations}），已执行 {context.current_iteration} 步。最后状态:\n{context.get_history_summary()}"


# ==================== 测试用例 ====================

def test_file_search_chain():
    print("=" * 60)
    print("测试1：文件搜索链式调用")
    print("用户请求：请查找 practice06 目录下所有包含'def'关键词的文件，并总结这些文件的主要内容")
    print("=" * 60)
    user_request = "请查找 practice06 目录下所有包含'def'关键词的文件，并总结这些文件的主要内容"
    answer = execute_chained_tool_call(user_request, max_iterations=10)
    print(f"\n测试1 结果: {answer}")
    return answer


def test_multi_file_operations():
    print("=" * 60)
    print("测试2：多文件操作")
    print("用户请求：读取 practice07 目录下的 1.txt 和 2.txt，把两个正整数相加的结果写入 result.txt")
    print("=" * 60)

    practice07_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    file1_path = os.path.join(practice07_dir, "1.txt")
    file2_path = os.path.join(practice07_dir, "2.txt")
    result_path = os.path.join(practice07_dir, "result.txt")

    if not os.path.exists(file1_path):
        with open(file1_path, 'w', encoding='utf-8') as f:
            f.write("42")
        print(f"[准备] 已创建测试文件 {file1_path}，内容: 42")
    if not os.path.exists(file2_path):
        with open(file2_path, 'w', encoding='utf-8') as f:
            f.write("58")
        print(f"[准备] 已创建测试文件 {file2_path}，内容: 58")

    user_request = f"读取 {file1_path} 和 {file2_path} 两个文件，文件内容都是正整数，把两个数相加的和写入 {result_path} 文件"
    answer = execute_chained_tool_call(user_request, max_iterations=10)

    if os.path.exists(result_path):
        with open(result_path, 'r', encoding='utf-8') as f:
            saved_content = f.read().strip()
        print(f"\n[验证] result.txt 内容: {saved_content}")
        try:
            expected = int(open(file1_path, 'r').read().strip()) + int(open(file2_path, 'r').read().strip())
            if saved_content == str(expected):
                print(f"[验证] 结果正确！{expected}")
            else:
                print(f"[验证] 结果不匹配，期望: {expected}，实际: {saved_content}")
        except Exception as e:
            print(f"[验证] 无法验证结果: {e}")

    print(f"\n测试2 结果: {answer}")
    return answer


def test_webpage_chain():
    print("=" * 60)
    print("测试3：网页处理链式调用")
    print("用户请求：访问指定网页并总结页面内容，保存到 practice07/summary.txt")
    print("=" * 60)

    practice07_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    summary_path = os.path.join(practice07_dir, "summary.txt")
    url = "https://www.nsu.edu.cn/HTML/news/2024/06/article_3974.html"

    user_request = f"访问 {url} 并总结页面内容，保存到 {summary_path}"
    answer = execute_chained_tool_call(user_request, max_iterations=10)

    if os.path.exists(summary_path):
        with open(summary_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        print(f"\n[验证] summary.txt 已保存，长度: {len(saved_content)} 字符")
    else:
        print(f"\n[验证] summary.txt 未成功创建")

    print(f"\n测试3 结果: {answer}")
    return answer


def run_all_tests():
    print("\n" + "=" * 60)
    print("开始运行所有链式调用测试")
    print("=" * 60)

    load_env()

    try:
        test_file_search_chain()
    except Exception as e:
        print(f"测试1 出错: {e}")

    try:
        test_multi_file_operations()
    except Exception as e:
        print(f"测试2 出错: {e}")

    try:
        test_webpage_chain()
    except Exception as e:
        print(f"测试3 出错: {e}")

    print("\n" + "=" * 60)
    print("所有测试运行完毕")
    print("=" * 60)


# ==================== 交互式主程序 ====================

def main():
    load_env()
    print("=" * 60)
    print("链式工具调用客户端 (Chained Tool Calls) — practice07")
    print("支持功能：")
    print("  - 文件搜索 (search_files) → 读取文件 (read_file) → 写入文件 (write_file)")
    print("  - 网页获取 (fetch_webpage) → 内容分析 → 保存结果")
    print("  - 多步骤自动串联，LLM 自主决策下一步操作")
    print()
    print("输入 'test' 运行所有测试用例")
    print("输入 'exit' / 'quit' 退出程序")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n>>> 你: ").strip()

            if user_input.lower() in ['exit', 'quit', '退出']:
                print("再见！")
                break
            if user_input.lower() == 'test':
                run_all_tests()
                continue
            if not user_input:
                continue

            print("\n[系统] 开始链式调用分析...")
            answer = execute_chained_tool_call(user_input, max_iterations=10)
            print(f"\n[助手] {answer}")

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"发生错误: {e}")


if __name__ == "__main__":
    main()
