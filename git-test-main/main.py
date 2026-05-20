# main.py
import os
import time
import requests
import json
from dotenv import load_dotenv
from practice04.anythingllm_tools import anythingllm_query

# 加载.env环境变量
load_dotenv()

# 从.env中读取配置
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")

# 工具定义
tools = [
    {
        "type": "function",
        "function": {
            "name": "anythingllm_query",
            "description": "查询文档仓库中的信息，当用户提到文档仓库、文件仓库、仓库时使用",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "要查询的内容"
                    }
                },
                "required": ["message"]
            }
        }
    }
]

# 系统提示词
system_prompt = """
你是一个智能助手，能够使用工具来帮助用户。

当用户提到以下内容时，请使用 anythingllm_query 工具：
- 文档仓库
- 文件仓库
- 仓库
- 文档
- 文件

工具参数说明：
- 工具名称：anythingllm_query
- 参数名称：message
- 参数值：用户的查询内容

当收到工具执行结果时，请将结果用自然语言总结给用户。
"""

def call_llm(messages, use_tools=True):
    """
    调用LLM模型
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    if use_tools:
        data["tools"] = tools
        data["tool_choice"] = "auto"
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"调用LLM失败: {e}")
        return None

def handle_tool_calls(tool_calls, messages):
    """
    处理工具调用
    """
    # 处理自定义工具调用格式
    if isinstance(tool_calls, dict) and "toolcall" in tool_calls:
        tool_call = tool_calls["toolcall"]
        function_name = tool_call["name"]
        arguments = tool_call["params"]
        
        if function_name == "anythingllm_query":
            # 处理参数名差异
            message = arguments.get("message", arguments.get("query"))
            print(f"[工具调用] anythingllm_query: {message}")
            
            # 调用AnythingLLM
            result = anythingllm_query(message)
            
            # 模拟工具响应消息
            messages.append({
                "role": "tool",
                "tool_call_id": "custom_tool_call",
                "name": function_name,
                "content": json.dumps(result)
            })
            
            # 再次调用LLM获取最终响应
            response = call_llm(messages, use_tools=False)
            if response:
                assistant_message = response["choices"][0]["message"]
                messages.append(assistant_message)
                return assistant_message["content"]
    
    # 处理标准OpenAI工具调用格式
    elif isinstance(tool_calls, list):
        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            
            if function_name == "anythingllm_query":
                message = arguments.get("message")
                print(f"[工具调用] anythingllm_query: {message}")
                
                # 调用AnythingLLM
                result = anythingllm_query(message)
                
                # 添加工具响应到消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": function_name,
                    "content": json.dumps(result)
                })
                
                # 再次调用LLM获取最终响应
                response = call_llm(messages, use_tools=False)
                if response:
                    assistant_message = response["choices"][0]["message"]
                    messages.append(assistant_message)
                    return assistant_message["content"]
    
    return "工具调用失败"

def chat_with_anythingllm():
    """
    聊天函数，支持AnythingLLM查询
    """
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    print("=" * 60)
    print("智能聊天（支持文档仓库查询）")
    print("=" * 60)
    print("当提到文档仓库、文件仓库、仓库时，会自动查询AnythingLLM")
    print("输入 'quit' 退出")
    print("=" * 60)
    print("\n开始聊天:\n")
    
    while True:
        user_input = input("你: ").strip()
        
        if user_input.lower() == "quit":
            print("\n感谢使用，再见！")
            break
        
        if not user_input:
            continue
        
        # 添加用户消息
        messages.append({"role": "user", "content": user_input})
        
        # 调用LLM
        print("[系统] 正在生成回复...")
        response = call_llm(messages)
        
        if response:
            assistant_message = response["choices"][0]["message"]
            
            # 检查是否有工具调用
            if "tool_calls" in assistant_message:
                # 处理标准工具调用格式
                tool_response = handle_tool_calls(assistant_message["tool_calls"], messages)
                print(f"助手: {tool_response}")
            elif "toolcall" in assistant_message:
                # 处理自定义工具调用格式
                tool_response = handle_tool_calls(assistant_message, messages)
                print(f"助手: {tool_response}")
            else:
                # 直接回复
                messages.append(assistant_message)
                print(f"助手: {assistant_message['content']}")
        else:
            print("[错误] LLM调用失败")

def test_anythingllm():
    """
    测试AnythingLLM连接
    """
    from practice04.anythingllm_tools import anythingllm_query
    
    print("=" * 60)
    print("测试AnythingLLM连接")
    print("=" * 60)
    
    result = anythingllm_query("测试连接")
    print(f"连接结果: {result}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test-anythingllm":
        test_anythingllm()
    else:
        chat_with_anythingllm()