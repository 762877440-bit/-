# practice03/chat_enhanced.py
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import openai

# ---------- 配置 ----------
# 创建新版 OpenAI 客户端
client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key = os.getenv("OPENROUTER_API_KEY")
)
MODEL = "nvidia/nemotron-3-super-120b-a12b:free"

# 触发压缩的阈值
COMPRESS_TOKEN_THRESHOLD = 3000
COMPRESS_ROUND_THRESHOLD = 5

# 关键信息提取的频率
KEY_INFO_EXTRACT_INTERVAL = 5

# 日志文件路径（可根据系统修改）
LOG_DIR = "D:/chat-log"
LOG_FILE = os.path.join(LOG_DIR, "log.txt")

# ---------- 辅助函数 ----------
def estimate_tokens(text: str) -> int:
    """估算文本的token数量"""
    return len(text) // 4

def count_total_tokens(messages: List[Dict[str, str]]) -> int:
    """计算消息列表的总token数"""
    total = 0
    for msg in messages:
        total += estimate_tokens(msg.get("content", ""))
    return total

def count_conversation_rounds(messages: List[Dict[str, str]]) -> int:
    """统计对话轮次"""
    rounds = 0
    for msg in messages:
        if msg.get("role") == "user":
            rounds += 1
    return rounds

def compress_history(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    对前70%历史进行摘要压缩，后30%保留原文。
    返回压缩后的新消息列表。
    """
    if len(messages) <= 2:
        return messages

    split_idx = int(len(messages) * 0.7)
    old_part = messages[:split_idx]
    recent_part = messages[split_idx:]

    # 构造压缩提示词
    old_text = "\n".join([f"{m['role']}: {m['content']}" for m in old_part])
    prompt = f"请将以下对话历史总结为一段简短的摘要，保留关键信息与上下文逻辑：\n{old_text}"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"摘要生成失败: {e}")
        return messages

    # 构建新的消息列表：摘要作为系统消息，后接最近30%原文
    new_messages = [{"role": "system", "content": f"对话历史摘要：{summary}"}]
    new_messages.extend(recent_part)
    return new_messages

def extract_key_info(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    提取关键信息，按照5W规则
    """
    if len(messages) < 2:
        return []

    # 构造提取提示词
    conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    prompt = f"请从以下对话中提取关键信息，按照5W规则（谁Who、做了什么事What、什么时候When、在何处Where、为什么要做这个事Why）进行提取。\n\n{conversation_text}\n\n请以JSON格式返回，每个关键信息为一个对象，包含字段：who, what, when, where, why。如果某些字段信息不足，可以留空字符串。"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()

        # 提取JSON部分
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            key_info_list = json.loads(json_match.group(0))
            if not isinstance(key_info_list, list):
                key_info_list = [key_info_list]
            return key_info_list
        else:
            return []
    except Exception as e:
        print(f"关键信息提取失败: {e}")
        return []

def save_key_info(key_info_list: List[Dict[str, str]]):
    """
    保存关键信息到日志文件
    """
    # 确保目录存在
    os.makedirs(LOG_DIR, exist_ok=True)

    # 写入日志
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n=== 关键信息提取 [{timestamp}] ===\n")

        for i, info in enumerate(key_info_list, 1):
            f.write(f"\n{'.' * 40}\n")
            f.write(f"关键信息 #{i}:\n")
            f.write(f"Who: {info.get('who', '')}\n")
            f.write(f"What: {info.get('what', '')}\n")
            f.write(f"When: {info.get('when', '')}\n")
            f.write(f"Where: {info.get('where', '')}\n")
            f.write(f"Why: {info.get('why', '')}\n")

        f.write(f"{'=' * 40}\n")

def should_search_history(user_input: str) -> bool:
    """
    判断是否需要搜索聊天历史
    """
    # 检查是否以 /search 开头
    if user_input.strip().startswith("/search"):
        return True

    # 检查是否表达了查找聊天历史的意思
    search_keywords = ["查找聊天历史", "搜索历史", "历史记录", "之前的对话", "之前说过"]
    for keyword in search_keywords:
        if keyword in user_input:
            return True

    return False

def search_chat_history(user_query: str) -> str:
    """
    搜索聊天历史
    """
    if not os.path.exists(LOG_FILE):
        return "没有找到聊天历史记录。"

    # 读取日志文件
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        log_content = f.read()

    # 构造搜索提示词
    prompt = f"请根据以下聊天历史记录，回答用户的问题：\n\n【聊天历史】\n{log_content}\n\n【用户问题】\n{user_query}"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"搜索失败: {e}"

# ---------- 命令行界面 ----------
def chat_with_enhanced_features():
    """命令行聊天界面，支持上下文压缩、关键信息提取和历史搜索"""
    messages = [{"role": "system", "content": "你是一个有用的助手。"}]

    print("=" * 60)
    print("智能聊天（增强版）")
    print("=" * 60)
    print(f"触发压缩: 对话超过{COMPRESS_ROUND_THRESHOLD}轮 或 上下文超过{COMPRESS_TOKEN_THRESHOLD} tokens")
    print(f"关键信息提取: 每{KEY_INFO_EXTRACT_INTERVAL}轮提取一次")
    print("搜索功能: 输入 /search 开头的内容或包含'查找聊天历史'等关键词")
    print("=" * 60)
    print("\n开始聊天（输入 'quit' 退出）:\n")

    while True:
        user_input = input("你: ").strip()

        if user_input.lower() == "quit":
            print("\n感谢使用，再见！")
            break

        if not user_input:
            continue

        # 检查是否需要搜索聊天历史
        if should_search_history(user_input):
            print("[系统] 正在搜索聊天历史...")
            search_result = search_chat_history(user_input)
            print(f"[搜索结果] {search_result}")
            continue

        # 添加用户消息
        messages.append({"role": "user", "content": user_input})

        # 检查是否需要压缩
        rounds = count_conversation_rounds(messages)
        tokens = count_total_tokens(messages)

        if rounds > COMPRESS_ROUND_THRESHOLD or tokens > COMPRESS_TOKEN_THRESHOLD:
            print(f"[系统] 上下文过长（轮次: {rounds}, tokens: {tokens}），正在压缩历史记录...")
            messages = compress_history(messages)
            print(f"[系统] 压缩完成，当前消息数: {len(messages)}")

        # 检查是否需要提取关键信息
        if rounds % KEY_INFO_EXTRACT_INTERVAL == 0 and rounds > 0:
            print("[系统] 正在提取关键信息...")
            key_info_list = extract_key_info(messages)
            if key_info_list:
                save_key_info(key_info_list)
                print(f"[系统] 关键信息提取完成，已保存到 {LOG_FILE}")
            else:
                print("[系统] 未提取到关键信息")

        # 调用LLM生成回复
        print("[系统] 正在生成回复...")
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.7,
            )
            full_response = response.choices[0].message.content.strip()
        except Exception as e:
            full_response = f"[错误] LLM调用失败: {e}"

        # 添加助手回复
        messages.append({"role": "assistant", "content": full_response})

        # 显示回复
        print(f"助手: {full_response}")
        print(f"[状态] 当前轮次: {count_conversation_rounds(messages)}, 估计tokens: {count_total_tokens(messages)}")

# ---------- 主函数 ----------
if __name__ == "__main__":
    chat_with_enhanced_features()