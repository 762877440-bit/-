import os
import json
import http.client
import ssl
from urllib.parse import urlparse
import sys
import stat
import time

# 导入 AnythingLLM 工具
from anythingllm_tools import anythingllm_query

# 读取.env文件
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if not os.path.exists(env_path):
        print(f"错误：{env_path} 文件不存在，请从 env.example 复制并填写正确参数")
        exit(1)
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value

# 工具函数1：列出某个目录下的文件（包括基本属性、大小等信息）
def list_files(directory):
    try:
        files = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            stat_info = os.stat(item_path)
            files.append({
                "name": item,
                "path": item_path,
                "size": stat_info.st_size,
                "mode": stat.filemode(stat_info.st_mode),
                "mtime": stat_info.st_mtime
            })
        return json.dumps({"status": "success", "data": files}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

# 工具函数2：修改某个目录下某个文件的名字
def rename_file(directory, old_name, new_name):
    try:
        old_path = os.path.join(directory, old_name)
        new_path = os.path.join(directory, new_name)
        os.rename(old_path, new_path)
        return json.dumps({"status": "success", "message": f"文件已重命名为 {new_name}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

# 工具函数3：删除某个目录下的某个文件
def delete_file(directory, file_name):
    try:
        file_path = os.path.join(directory, file_name)
        os.remove(file_path)
        return json.dumps({"status": "success", "message": "文件已删除"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

# 工具函数4：在某个目录下新建1个文件，并且写入内容
def create_file(directory, file_name, content):
    try:
        file_path = os.path.join(directory, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"status": "success", "message": "文件已创建"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

# 工具函数5：读取某个目录下的某个文件的内容
def read_file(directory, file_name):
    try:
        file_path = os.path.join(directory, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return json.dumps({"status": "success", "data": content}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

# 工具函数6：访问网页并返回内容
def fetch_webpage(url):
    try:
        # 清理URL中的反引号
        url = url.strip('`')
        # 解析URL
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        # 对路径进行URL编码，处理中文字符
        from urllib.parse import quote
        path = parsed_url.path if parsed_url.path else '/'
        # 确保路径正确编码
        path = quote(path, safe='/')
        if parsed_url.query:
            path += '?' + parsed_url.query
        protocol = parsed_url.scheme
        
        # 根据协议选择连接类型
        if protocol == 'https':
            # 创建不验证证书的 SSL 上下文
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            conn = http.client.HTTPSConnection(host, context=context)
        else:
            conn = http.client.HTTPConnection(host)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        conn.request('GET', path, headers=headers)
        response = conn.getresponse()
        content = response.read().decode('utf-8', errors='replace')
        
        # 限制返回内容大小，避免超过LLM处理限制
        max_content_length = 100000  # 100KB
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n... (内容已截断)"
        
        return json.dumps({"status": "success", "data": content}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

# 工具函数7：搜索聊天历史
def search_chat_history(query):
    try:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history.log')
        if not os.path.exists(log_path):
            return json.dumps({"status": "error", "message": "聊天历史文件不存在"}, ensure_ascii=False)
        
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        search_prompt = f"用户查询: {query}\n\n聊天历史记录:\n{content}\n\n请根据聊天历史回答用户的问题，重点关注与查询相关的信息。"
        
        return json.dumps({"status": "success", "data": search_prompt}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

# 调用LLM API（非流式，用于工具调用）
def call_llm(messages, tools=None):
    # 获取配置
    base_url = os.getenv('BASE_URL')
    model = os.getenv('MODEL')
    api_key = os.getenv('API_KEY')
    
    if not all([base_url, model, api_key]):
        print("错误：请在.env文件中配置BASE_URL、MODEL和API_KEY")
        exit(1)
    
    # 解析URL
    parsed_url = urlparse(base_url)
    host = parsed_url.netloc
    path = parsed_url.path.rstrip('/') + '/chat/completions'
    protocol = parsed_url.scheme
    
    # 准备请求数据
    data = {
        "model": model,
        "messages": messages,
        "temperature": float(os.getenv('TEMPERATURE', '0.7')),
        "max_tokens": int(os.getenv('MAX_TOKENS', '8192'))
    }
    
    # 如果提供了工具，添加到请求中
    if tools:
        data["tools"] = tools
        data["tool_choice"] = "auto"
    
    # 根据协议选择连接类型
    if protocol == 'https':
        # 创建不验证证书的 SSL 上下文
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
        
        # 尝试解析为JSON
        try:
            response_data = json.loads(response_content)
        except json.JSONDecodeError:
            # 如果解析失败，直接返回响应内容作为字符串
            if response.status == 200:
                return response_content
            else:
                print(f"API错误: {response_content}")
                return None
        
        if response.status == 200:
            return response_data
        else:
            # 无论response_data是什么类型，都安全处理
            if isinstance(response_data, dict):
                error_info = response_data.get('error', {})
                if isinstance(error_info, dict):
                    error_message = error_info.get('message', '未知错误')
                else:
                    error_message = str(error_info)
            else:
                error_message = str(response_data)
            print(f"API错误: {error_message}")
            return None
    finally:
        conn.close()

# 流式调用LLM API（用于普通对话）
def stream_llm(messages):
    # 获取配置
    base_url = os.getenv('BASE_URL')
    model = os.getenv('MODEL')
    api_key = os.getenv('API_KEY')
    
    if not all([base_url, model, api_key]):
        print("错误：请在.env文件中配置BASE_URL、MODEL和API_KEY")
        exit(1)
    
    # 解析URL
    parsed_url = urlparse(base_url)
    host = parsed_url.netloc
    path = parsed_url.path.rstrip('/') + '/chat/completions'
    protocol = parsed_url.scheme
    
    # 准备请求数据
    data = {
        "model": model,
        "messages": messages,
        "temperature": float(os.getenv('TEMPERATURE', '0.7')),
        "max_tokens": int(os.getenv('MAX_TOKENS', '8192')),
        "stream": True
    }
    
    # 根据协议选择连接类型
    if protocol == 'https':
        # 创建不验证证书的 SSL 上下文
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
        
        # 处理流式响应
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
        print()  # 换行
        return full_response
    finally:
        conn.close()

# 执行工具调用
def execute_tool_call(tool_call):
    # 解析OpenAI格式的工具调用
    if tool_call.get('type') == 'function':
        function = tool_call.get('function', {})
        tool_name = function.get('name')
        # 解析arguments（可能是字符串或对象）
        arguments = function.get('arguments', {})
        if isinstance(arguments, str):
            try:
                tool_args = json.loads(arguments)
            except json.JSONDecodeError:
                tool_args = {}
        else:
            tool_args = arguments
    else:
        # 兼容其他格式
        tool_name = tool_call.get('name')
        tool_args = tool_call.get('arguments', {})
    
    print(f"执行工具: {tool_name}")
    print(f"参数: {tool_args}")
    
    if tool_name == "list_directory":
        path = tool_args.get('path')
        result = list_files(path)
    elif tool_name == "rename_file":
        directory = tool_args.get('directory')
        old_name = tool_args.get('old_name')
        new_name = tool_args.get('new_name')
        result = rename_file(directory, old_name, new_name)
    elif tool_name == "delete_file":
        directory = tool_args.get('directory')
        file_name = tool_args.get('file_name')
        result = delete_file(directory, file_name)
    elif tool_name == "create_file":
        directory = tool_args.get('directory')
        file_name = tool_args.get('file_name')
        content = tool_args.get('content')
        result = create_file(directory, file_name, content)
    elif tool_name == "read_file":
        directory = tool_args.get('directory')
        file_name = tool_args.get('file_name')
        result = read_file(directory, file_name)
    elif tool_name == "fetch_webpage":
        url = tool_args.get('url')
        result = fetch_webpage(url)
    elif tool_name == "search_chat_history":
        query = tool_args.get('query')
        result = search_chat_history(query)
    elif tool_name == "query_anythingllm":
        question = tool_args.get('question')
        res = anythingllm_query(question)
        if res.get("success"):
            result = json.dumps({"status": "success", "data": res.get("content", "")}, ensure_ascii=False)
        else:
            result = json.dumps({"status": "error", "message": res.get("error", "未知错误")}, ensure_ascii=False)
    else:
        result = f"错误：未知的工具 {tool_name}"
    
    print(f"工具执行结果: {result}")
    return result

def summarize_chat_history(chat_history):
    """总结聊天历史，压缩前70%的内容，保留最后30%的原文"""
    # 过滤掉系统消息，只保留用户和助手的消息
    user_assistant_messages = [msg for msg in chat_history if msg['role'] in ['user', 'assistant']]
    
    if len(user_assistant_messages) <= 2:
        return chat_history
    
    # 计算分割点
    split_point = int(len(user_assistant_messages) * 0.7)
    messages_to_summarize = user_assistant_messages[:split_point]
    messages_to_keep = user_assistant_messages[split_point:]
    
    # 构建总结提示
    summary_prompt = "请对以下聊天记录进行总结，提取关键信息和主要内容：\n\n"
    for msg in messages_to_summarize:
        role = "用户" if msg['role'] == 'user' else "助手"
        summary_prompt += f"{role}: {msg['content']}\n\n"
    
    # 调用LLM进行总结
    summary_messages = [
        {"role": "system", "content": "你是一个聊天记录总结助手，需要对聊天内容进行简洁明了的总结。"},
        {"role": "user", "content": summary_prompt}
    ]
    
    summary_response = call_llm(summary_messages)
    if summary_response and isinstance(summary_response, dict):
        summary = summary_response.get('choices', [{}])[0].get('message', {}).get('content', '')
    else:
        # 如果返回的不是预期的JSON格式，尝试直接使用响应内容
        if isinstance(summary_response, str):
            summary = summary_response
        else:
            summary = "聊天记录总结失败"
    
    # 构建新的聊天历史
    new_chat_history = [chat_history[0]]  # 保留系统提示
    new_chat_history.append({"role": "assistant", "content": f"【聊天记录总结】: {summary}"})
    new_chat_history.extend(messages_to_keep)
    
    return new_chat_history

def extract_key_info(chat_history):
    """提取聊天关键信息，按照5W规则"""
    # 过滤掉系统消息和总结消息
    relevant_messages = [msg for msg in chat_history if msg['role'] in ['user', 'assistant'] and not msg.get('content', '').startswith('【聊天记录总结】')]
    
    # 构建提取提示
    extract_prompt = "请从以下聊天记录中提取关键信息，按照5W规则（谁Who、做了什么事What、什么时候When、在何处Where、为什么要做这个事Why）提取多条关键信息：\n\n"
    for msg in relevant_messages:
        role = "用户" if msg['role'] == 'user' else "助手"
        extract_prompt += f"{role}: {msg['content']}\n\n"
    
    # 调用LLM进行提取
    extract_messages = [
        {"role": "system", "content": "你是一个信息提取助手，需要从聊天记录中按照5W规则提取关键信息。"},
        {"role": "user", "content": extract_prompt}
    ]
    
    extract_response = call_llm(extract_messages)
    if extract_response and isinstance(extract_response, dict):
        key_info = extract_response.get('choices', [{}])[0].get('message', {}).get('content', '')
    else:
        # 如果返回的不是预期的JSON格式，尝试直接使用响应内容
        if isinstance(extract_response, str):
            key_info = extract_response
        else:
            key_info = "关键信息提取失败"
    
    # 写入log.txt文件
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history.log')
    # 确保目录存在
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # 追加写入
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        f.write(key_info)
        f.write("\n")
    
    return key_info

def main():
    # 加载环境变量
    load_env()
    
    # 定义工具
    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "列出指定目录下的所有文件和目录，包括基本属性",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "目录路径"
                        }
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "rename_file",
                "description": "修改指定目录下的文件名称",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "目录路径"
                        },
                        "old_name": {
                            "type": "string",
                            "description": "原文件名"
                        },
                        "new_name": {
                            "type": "string",
                            "description": "新文件名"
                        }
                    },
                    "required": ["directory", "old_name", "new_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delete_file",
                "description": "删除指定目录下的文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "目录路径"
                        },
                        "file_name": {
                            "type": "string",
                            "description": "文件名"
                        }
                    },
                    "required": ["directory", "file_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_file",
                "description": "在指定目录下创建新文件并写入内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "目录路径"
                        },
                        "file_name": {
                            "type": "string",
                            "description": "文件名"
                        },
                        "content": {
                            "type": "string",
                            "description": "文件内容"
                        }
                    },
                    "required": ["directory", "file_name", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "读取指定目录下的文件内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "目录路径"
                        },
                        "file_name": {
                            "type": "string",
                            "description": "文件名"
                        }
                    },
                    "required": ["directory", "file_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "fetch_webpage",
                "description": "访问指定URL的网页并返回内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "网页URL"
                        }
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_chat_history",
                "description": "搜索聊天历史记录，当用户输入以'/search'开头或表达'查找聊天历史'的意思时使用",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_anythingllm",
                "description": "查询AnythingLLM工作区中的文档。当用户询问关于上传到AnythingLLM工作区中的文件内容时，使用此工具。例如：'帮我查找工作区文档中关于XX的内容'、'总结上传的文档'等。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "要向AnythingLLM工作区提问的问题"
                        }
                    },
                    "required": ["question"]
                }
            }
        }
    ]
    
    # 系统提示词
    system_prompt = """你是一个具有文件操作、网络访问、聊天历史搜索以及AnythingLLM文档查询能力的AI助手，能够执行以下操作：

1. 列出目录内容：使用 list_directory 工具查看指定目录下的文件和目录
2. 重命名文件：使用 rename_file 工具修改文件名称
3. 删除文件：使用 delete_file 工具删除指定文件
4. 创建文件：使用 create_file 工具创建新文件并写入内容
5. 读取文件：使用 read_file 工具读取指定文件的内容
6. 访问网页：使用 fetch_webpage 工具访问指定URL的网页并获取内容
7. 搜索聊天历史：使用 search_chat_history 工具搜索聊天历史记录
8. 查询AnythingLLM工作区文档：使用 query_anythingllm 工具，参数 question 填写你的问题。当用户询问关于你上传到AnythingLLM工作区中的文件内容时，务必使用此工具，不要自己编造答案。

当用户请求涉及文件操作或需要访问网页时，请使用相应的工具进行操作，不要自行猜测或模拟结果。

当用户输入以'/search'开头，或表达了'查找聊天历史'的意思，或你认为应该查找聊天历史时，请使用 search_chat_history 工具。

当用户询问关于上传文档的内容、要求总结文档、查找文档中的特定信息时，请使用 query_anythingllm 工具。

工具使用格式：
- 思考：分析用户需求，确定需要使用的工具
- 工具调用：使用指定的工具函数和参数
- 结果处理：根据工具执行结果向用户提供反馈

当使用 fetch_webpage 工具获取网页内容后，你可以对内容进行总结，提取关键信息，或根据用户需求进行分析。"""
    
    # 初始化聊天历史
    chat_history = [
        {"role": "system", "content": system_prompt}
    ]
    
    # 聊天轮数计数器
    chat_rounds = 0
    
    print("=== LLM 工具调用客户端 ===")
    print("输入消息开始聊天，按 Ctrl+C 退出")
    print("=======================")
    print("可用工具：list_files, rename_file, delete_file, create_file, read_file, fetch_webpage, search_chat_history, query_anythingllm")
    print()
    print("示例：")
    print("1. 列出目录内容：列出当前目录的文件")
    print("2. 访问网页：访问 https://www.example.com 并总结内容")
    print("3. 搜索聊天历史：/search 我之前说了什么")
    print("4. 查询AnythingLLM文档：帮我查找工作区中关于[主题]的内容")
    print()
    
    try:
        while True:
            # 获取用户输入
            user_input = input("你: ")
            
            # 检查是否需要搜索聊天历史
            if user_input.startswith('/search') or '查找聊天历史' in user_input or '搜索聊天' in user_input:
                # 提取查询内容
                if user_input.startswith('/search'):
                    query = user_input[7:].strip()
                else:
                    query = user_input
                
                # 调用搜索工具
                tool_result = search_chat_history(query)
                
                # 解析结果
                result_data = json.loads(tool_result)
                if result_data.get('status') == 'success':
                    search_prompt = result_data.get('data', '')
                    # 调用LLM获取回答
                    search_messages = [
                        {"role": "system", "content": "你是一个聊天历史查询助手，需要根据聊天历史回答用户的问题。"},
                        {"role": "user", "content": search_prompt}
                    ]
                    print("助手: ", end='', flush=True)
                    search_response = stream_llm(search_messages)
                    if search_response:
                        chat_history.append({"role": "user", "content": user_input})
                        chat_history.append({"role": "assistant", "content": search_response})
                else:
                    print("助手: ", end='', flush=True)
                    print(result_data.get('message', '搜索失败'))
                    chat_history.append({"role": "user", "content": user_input})
                    chat_history.append({"role": "assistant", "content": result_data.get('message', '搜索失败')})
            else:
                # 添加用户消息到历史
                chat_history.append({"role": "user", "content": user_input})
                chat_rounds += 1
                
                # 检查是否需要总结聊天历史
                # 计算聊天历史长度
                history_length = sum(len(str(msg.get('content', ''))) for msg in chat_history)
                # 过滤掉系统消息和工具消息，计算实际聊天轮数
                actual_rounds = len([msg for msg in chat_history if msg['role'] in ['user', 'assistant']])
                
                if actual_rounds > 5 or history_length > 3000:
                    print("正在总结聊天历史...")
                    chat_history = summarize_chat_history(chat_history)
                
                # 检查是否需要提取关键信息
                if chat_rounds % 5 == 0:
                    print("正在提取关键信息...")
                    extract_key_info(chat_history)
                
                # 显示助手回复
                print("助手: ", end='', flush=True)
                
                # 调用LLM（带工具）
                try:
                    response = call_llm(chat_history, tools)
                    
                    if not response:
                        print("请求失败")
                        continue
                except Exception as e:
                    print(f"请求异常: {str(e)}")
                    continue
                
                # 处理响应
                if isinstance(response, dict):
                    choice = response.get('choices', [{}])[0]
                    message = choice.get('message', {})
                    
                    # 检查是否有工具调用
                    if message.get('tool_calls'):
                        # 处理工具调用
                        for tool_call in message.get('tool_calls', []):
                            # 执行工具
                            tool_result = execute_tool_call(tool_call)
                            
                            # 添加助手消息（工具调用）到历史
                            chat_history.append(message)
                            
                            # 添加工具执行结果到历史
                            chat_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.get('id'),
                                "name": tool_call.get('function', {}).get('name'),
                                "content": json.dumps(tool_result, ensure_ascii=False)
                            })
                        
                        # 再次调用LLM获取最终响应
                        final_response = stream_llm(chat_history)
                        if final_response:
                            # 添加最终回复到历史
                            chat_history.append({"role": "assistant", "content": final_response})
                    else:
                        # 普通响应
                        content = message.get('content', '')
                        print(content)
                        # 添加助手回复到历史
                        chat_history.append(message)
                else:
                    # 如果响应是字符串，直接显示
                    print(response)
                    # 添加助手回复到历史
                    chat_history.append({"role": "assistant", "content": response})
            
            print()  # 空行分隔
    except KeyboardInterrupt:
        print("\n退出工具调用客户端")
        sys.exit(0)

if __name__ == "__main__":
    main()