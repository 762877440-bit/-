import os
import time
import requests
from dotenv import load_dotenv
# 1. 加载.env环境变量
load_dotenv()  # 自动读取同目录下的.env文件
# 2. 从.env中读取配置
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")
# 3. 构造请求头和请求体
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}
data = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
    "temperature": 0.7,
    "max_tokens": 512
}
# 4. 发送请求并统计耗时
print(f"正在调用本地模型 {MODEL}...")
start_time = time.time()
response = requests.post(
    f"{BASE_URL}/chat/completions",
    headers=headers,
    json=data
)
end_time = time.time()
elapsed = end_time - start_time
# 5. 解析响应并输出结果
if response.status_code == 200:
    result = response.json()
    answer = result["choices"][0]["message"]["content"]
    prompt_tokens = result["usage"]["prompt_tokens"]
    completion_tokens = result["usage"]["completion_tokens"]
    total_tokens = result["usage"]["total_tokens"]
    speed = completion_tokens / elapsed if elapsed > 0 else 0
    print("\n=== 模型回答 ===")
    print(answer)
    print("\n=== 性能统计 ===")
    print(f"总耗时: {elapsed:.2f} 秒")
    print(f"输入token: {prompt_tokens}, 输出token: {completion_tokens}, 总token: {total_tokens}")
    print(f"生成速度: {speed:.2f} token/s")
else:
    print(f"请求失败，状态码: {response.status_code}")
    print(f"错误信息: {response.text}")


def demo_network_operations():
    """
    演示网络访问功能
    """
    from practice02.network_operations import curl_get, curl_post
    
    print("\n" + "="*60)
    print("网络访问功能演示")
    print("="*60)
    
    print("\n1. 测试GET请求 - 访问example.com...")
    result = curl_get("https://www.example.com", timeout=10)
    if result.get("success"):
        print(f"[OK] 状态码: {result.get('status_code')}")
        print(f"[OK] 耗时: {result.get('elapsed_time')}秒")
        print(f"[OK] 内容长度: {result.get('content_length')}字节")
        print(f"[OK] 内容类型: {result.get('content_type')}")
    else:
        print(f"[ERROR] {result.get('error')}")
    
    print("\n2. 测试GET请求 - 访问JSON API...")
    result = curl_get("https://jsonplaceholder.typicode.com/posts/1")
    if result.get("success"):
        print(f"[OK] 状态码: {result.get('status_code')}")
        print(f"[OK] 内容类型: {result.get('content_type_category')}")
        print(f"[OK] JSON内容: {result.get('content')}")
    else:
        print(f"[ERROR] {result.get('error')}")
    
    print("\n3. 测试POST请求...")
    result = curl_post(
        "https://jsonplaceholder.typicode.com/posts",
        json_data={
            "title": "测试标题",
            "body": "测试内容",
            "userId": 1
        }
    )
    if result.get("success"):
        print(f"[OK] 状态码: {result.get('status_code')}")
        print(f"[OK] 响应内容: {result.get('content')}")
    else:
        print(f"[ERROR] {result.get('error')}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--network":
        demo_network_operations()
    else:
        pass