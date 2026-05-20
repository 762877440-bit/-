# Practice05 高级工具调用系统

本项目实现了一个高级工具调用系统，支持文件操作、网页访问、聊天历史管理、文档仓库查询和可扩展的技能系统。

## 项目结构

```
practice05/
├── .agents/
│   └── skills/
│       └── notice/
│           └── SKILL.md          # 通知撰写技能定义
├── anythingllm_tools.py           # AnythingLLM文档仓库查询工具
├── tool_client.py                # 主程序（工具调用客户端）
└── README.md                     # 本文档
```

## 功能特性

### 1. 文件操作工具

提供5个核心文件操作功能：

| 工具名称 | 功能描述 |
|---------|---------|
| `list_directory` | 列出目录下所有文件及属性（名称、路径、大小、权限、修改时间） |
| `rename_file` | 重命名指定目录下的文件 |
| `delete_file` | 删除指定目录下的文件 |
| `create_file` | 创建新文件并写入内容（UTF-8编码） |
| `read_file` | 读取指定文件的内容 |

### 2. 网页访问工具

| 工具名称 | 功能描述 |
|---------|---------|
| `fetch_webpage` | 访问指定URL的网页并获取内容，支持HTTPS，自动处理中文URL编码 |

### 3. 聊天历史管理

| 工具名称 | 功能描述 |
|---------|---------|
| `search_chat_history` | 搜索聊天历史记录，结合用户查询和历史内容进行智能回答 |

**自动管理功能：**

- **聊天记录总结** (`summarize_chat_history`)：当聊天超过5轮或上下文过长时，自动触发LLM总结聊天记录，压缩前70%内容保留关键信息
- **关键信息提取** (`extract_key_info`)：按照5W规则（谁Who、做什么What、什么时候When、在何处Where、为什么Why）提取关键信息并记录到本地文件

### 4. AnythingLLM文档仓库查询

| 工具名称 | 功能描述 |
|---------|---------|
| `query_anythingllm` | 查询AnythingLLM文档仓库中的信息，支持智能问答 |

**配置环境变量：**

```bash
ANYTHINGLLM_API_KEY=your_api_key
ANYTHINGLLM_WORKSPACE_SLUG=your_workspace_slug
ANYTHINGLLM_BASE_URL=http://localhost:3001
```

### 5. 技能系统（可扩展）

| 工具名称 | 功能描述 |
|---------|---------|
| `load_skill_content` | 加载指定技能的正文章内容，用于辅助生成 |

**技能定义规范：**

技能文件位于 `.agents/skills/` 目录下，每个技能一个文件夹，包含 `SKILL.md` 文件。

`SKILL.md` 文件格式：

```markdown
---
name: skill_name
description: 技能描述，说明何时使用该技能
---

# 技能正文

技能的使用规范和详细内容说明...
```

**内置技能：**

- `notice`：通知撰写技能
  - 通知不能以"通知"二字开头
  - 必须以"XX部通知"格式书写
  - 如用户未提供部门信息，默认使用"XX部"

## 工具列表

| 序号 | 工具名称 | 功能说明 |
|-----|---------|---------|
| 1 | list_directory | 列出目录内容 |
| 2 | rename_file | 重命名文件 |
| 3 | delete_file | 删除文件 |
| 4 | create_file | 创建文件 |
| 5 | read_file | 读取文件 |
| 6 | fetch_webpage | 访问网页 |
| 7 | search_chat_history | 搜索聊天历史 |
| 8 | query_anythingllm | 查询文档仓库 |
| 9 | load_skill_content | 加载技能内容 |

## 使用方法

### 环境配置

1. 在项目根目录创建 `.env` 文件
2. 配置必要的环境变量：

```bash
# LLM API配置
BASE_URL=http://localhost:8000
API_KEY=your_api_key
MODEL=your_model_name
TEMPERATURE=0.7
MAX_TOKENS=8192

# AnythingLLM配置
ANYTHINGLLM_API_KEY=your_anythingllm_api_key
ANYTHINGLLM_WORKSPACE_SLUG=mywork
ANYTHINGLLM_BASE_URL=http://localhost:3001

# 聊天历史记录路径
CHAT_LOG_PATH=/Users/atfa/Desktop/实验报告/log.txt
```

### 运行程序

```bash
cd practice05
python tool_client.py
```

### 添加新技能

1. 在 `.agents/skills/` 目录下创建新的技能文件夹
2. 创建 `SKILL.md` 文件，定义技能名称、描述和正文内容
3. 在系统提示词中说明新技能的触发条件

## 技术实现

### 工具调用流程

1. **用户输入** → 构建消息列表
2. **LLM分析** → 判断是否需要调用工具
3. **工具选择** → 根据LLM返回的function_call执行对应工具
4. **结果处理** → 将工具执行结果反馈给LLM
5. **最终回复** → LLM整合后生成最终回答

### 聊天压缩机制

当聊天轮次超过5轮或上下文长度超过阈值时：
- 自动调用 `summarize_chat_history` 压缩前70%内容
- 保留最近30%的对话原文
- 生成总结作为系统消息插入

### 关键信息提取

按照5W规则从聊天记录中提取关键信息：
- **Who（谁）**：执行动作的主体
- **What（什么）**：执行的动作或事件
- **When（何时）**：时间信息
- **Where（何地）**：地点信息
- **Why（为何）**：原因和目的

提取结果追加写入聊天历史记录文件。

## 注意事项

1. **API超时设置**：本地模型响应较慢，默认超时时间设置为120秒
2. **内容截断**：网页内容超过100KB时自动截断，避免超出LLM处理限制
3. **路径处理**：支持中文字符路径，自动进行URL编码
4. **错误处理**：所有工具都包含完善的异常捕获和错误信息返回
5. **编码格式**：文件操作统一使用UTF-8编码

## 扩展开发

### 添加新工具

1. 在 `tool_client.py` 中定义工具函数
2. 在 `tools` 列表中添加工具定义（OpenAI function call格式）
3. 在 `execute_tool_call` 函数中添加工具执行分支
4. 更新系统提示词说明新工具的用途

### 添加新技能

1. 在 `.agents/skills/` 下创建技能目录
2. 编写 `SKILL.md` 文件，定义技能元数据和正文
3. 技能系统会自动扫描并加载可用技能

## 示例对话

```
用户: 帮我重命名 test.txt 为 demo.txt
执行工具: rename_file
参数: {"directory": ".", "old_name": "test.txt", "new_name": "demo.txt"}
工具执行结果: {"status": "success", "message": "文件已重命名为 demo.txt"}
助手: 已成功将 test.txt 重命名为 demo.txt。

用户: 文档仓库里有什么？
执行工具: query_anythingllm
参数: {"question": "文档仓库里有什么？"}
工具执行结果: {"status": "success", "data": "文档仓库包含项目文档、API文档和用户指南。"}
助手: 根据文档仓库的信息，里面包含项目文档、API文档和用户指南等内容。

用户: 帮我写一个放假通知
执行工具: load_skill_content
参数: {"skill_name": "notice"}
工具执行结果: [技能正文内容]
助手: 根据技能规范，放假通知应该以部门名称开头，不能直接使用"通知"二字...
```

## 依赖环境

- Python 3.7+
- requests
- python-dotenv
- PyYAML