# cli.py
import asyncio
import os
from typing import Optional


class CLI:
    COLOR_USER = "\033[32m"
    COLOR_AGENT = "\033[37m"
    COLOR_THINK = "\033[90m"
    COLOR_ERROR = "\033[31m"
    COLOR_RESET = "\033[0m"

    def __init__(self, agent, model_client):
        self.agent = agent
        self.model_client = model_client
        self.search_enabled = True
        self.message_history = []

    def print_color(self, text: str, color: str):
        print(f"{color}{text}{self.COLOR_RESET}")

    def print_user_input(self, text: str):
        self.print_color(f"You > {text}", self.COLOR_USER)

    def print_agent_response(self, text: str):
        self.print_color(f"Agent > {text}", self.COLOR_AGENT)

    def print_thinking(self, text: str):
        self.print_color(f"[思考] {text}", self.COLOR_THINK)

    def print_error(self, text: str):
        self.print_color(f"[错误] {text}", self.COLOR_ERROR)

    async def handle_command(self, command: str) -> bool:
        cmd = command.strip().lower()
        if cmd == "exit":
            print("\n感谢使用，再见！")
            return True
        elif cmd == "/clear":
            self.message_history = []
            os.system('cls' if os.name == 'nt' else 'clear')
            print("对话上下文已清空")
            return False
        elif cmd.startswith("/memory"):
            parts = cmd.split()
            if len(parts) > 1 and parts[1] == "delete":
                if len(parts) > 2:
                    keyword = " ".join(parts[2:])
                    if self.agent.memory_system.delete_memory(keyword):
                        print(f"已删除包含'{keyword}'的记忆")
                    else:
                        print(f"未找到包含'{keyword}'的记忆")
                else:
                    print("请指定要删除的关键词，如: /memory delete 关键词")
            else:
                memories = self.agent.memory_system.get_all_memories()
                if memories:
                    print("\n=== 已存储的记忆 ===")
                    for i, mem in enumerate(memories, 1):
                        print(f"{i}. {mem['content']}")
                    print("=== 记忆结束 ===\n")
                else:
                    print("暂无存储的记忆")
            return False
        elif cmd.startswith("/search"):
            parts = cmd.split()
            if len(parts) > 1:
                if parts[1] == "on":
                    self.search_enabled = True
                    print("搜索功能已开启")
                elif parts[1] == "off":
                    self.search_enabled = False
                    print("搜索功能已关闭")
                else:
                    print("无效的搜索命令，使用 /search on 或 /search off")
            else:
                status = "开启" if self.search_enabled else "关闭"
                print(f"搜索功能当前状态: {status}")
            return False
        elif cmd == "/help":
            print("\n=== 命令帮助 ===")
            print("exit          - 退出程序")
            print("/clear        - 清空对话上下文")
            print("/memory       - 查看已存储的记忆")
            print("/memory delete <关键词> - 删除包含关键词的记忆")
            print("/search on    - 开启搜索功能")
            print("/search off   - 关闭搜索功能")
            print("/help         - 显示此帮助信息")
            print("=== 命令结束 ===\n")
            return False
        else:
            return False

    async def chat_loop(self):
        """主聊天循环，使用 Agent 的流式输出"""
        print("=" * 60)
        print("欢迎使用 TerminalAI - 智能终端助手")
        print("输入 'exit' 退出，'/help' 查看帮助")
        print("=" * 60)

        while True:
            try:
                user_input = input(f"{self.COLOR_USER}You > {self.COLOR_RESET}").strip()
                if not user_input:
                    continue

                if await self.handle_command(user_input):
                    break

                self.print_thinking("正在处理请求...")
                try:
                    print(f"{self.COLOR_AGENT}Agent > {self.COLOR_RESET}", end="", flush=True)
                    full_response = ""
                    async for token in self.agent.run_stream(user_input, self.search_enabled):
                        print(token, end="", flush=True)
                        full_response += token
                    print()  # 换行
                    # 将本轮对话存入历史（仅用于显示，Agent内部记忆已独立存储）
                    self.message_history.append({"role": "user", "content": user_input})
                    self.message_history.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    print()
                    self.print_error(f"处理失败: {str(e)}")
                    # 降级直接调用模型
                    try:
                        print(f"{self.COLOR_AGENT}Agent > {self.COLOR_RESET}", end="", flush=True)
                        fallback_messages = [{"role": "system", "content": "你是一个专业的AI助手，使用中文回复。"},
                                             {"role": "user", "content": user_input}]
                        async for token in self.model_client.generate_stream(fallback_messages):
                            print(token, end="", flush=True)
                        print()
                    except Exception as fallback_e:
                        self.print_error(f"降级调用也失败: {str(fallback_e)}")
            except KeyboardInterrupt:
                print("\n\n感谢使用，再见！")
                break