<<<<<<< HEAD
# LLM Local Test 项目

本地LLM模型测试和工具函数学习项目

## 项目结构

```
LLM_local_test/
├── main.py                          # 主程序入口（支持AnythingLLM集成）
├── practice01/                      # 练习模块
│   ├── file_operations.py          # 文件操作工具
│   ├── network_operations.py       # 网络访问工具
│   ├── example_usage.py            # 使用示例
│   └── demo_files/                 # 演示文件目录
├── practice03/                      # 聊天增强模块
│   └── tool_client.py              # 增强版聊天程序
├── practice04/                      # AnythingLLM集成模块
│   ├── anythingllm_client.py       # AnythingLLM查询工具
│   └── tool_client.py              # 工具调用客户端
├── .gitignore                       # Git忽略文件
├── env.example                      # 环境变量示例
└── README.md                        # 项目说明文档
```

## 功能模块

### 1. 主程序 (main.py)

主程序用于调用本地LLM模型进行对话测试，支持AnythingLLM文档仓库查询。

**使用方法：**

```bash
# 调用LLM模型（支持AnythingLLM查询）
python main.py

# 测试网络访问功能
python main.py --network

# 测试AnythingLLM连接
python main.py --test-anythingllm
```

**功能特性：**

- 支持function call调用AnythingLLM工具
- 当用户提到"文档仓库"、"文件仓库"、"仓库"时自动触发查询
- 实时显示工具调用过程和结果
- 完善的错误处理
- 支持标准和自定义工具调用格式

**环境配置：**

1. 复制 `env.example` 为 `.env`
2. 配置以下环境变量：
   - `BASE_URL`: LLM API基础URL
   - `API_KEY`: API密钥
   - `MODEL`: 模型名称
   - `ANYTHINGLLM_API_KEY`: AnythingLLM API密钥（用于文档仓库查询）
   - `ANYTHINGLLM_WORKSPACE_SLUG`: AnythingLLM工作区slug
   - `ANYTHINGLLM_BASE_URL`: AnythingLLM服务基础URL（默认：http://localhost:3001）

### 2. 文件操作工具 (practice01/file_operations.py)

提供5个核心文件操作功能：

#### 功能列表

1. **list_directory_files(directory_path)**
   - 列出目录下所有文件及其属性
   - 返回文件名、大小、类型、时间戳等信息

2. **rename_file(directory_path, old_name, new_name)**
   - 重命名指定目录下的文件
   - 包含文件存在性检查

3. **delete_file(directory_path, filename)**
   - 删除指定目录下的文件
   - 支持删除文件和空目录

4. **create_file_with_content(directory_path, filename, content)**
   - 创建新文件并写入内容
   - UTF-8编码，自动检测文件是否已存在

5. **read_file_content(directory_path, filename)**
   - 读取文件内容
   - 返回文件内容和元数据

**使用示例：**

```python
from practice01.file_operations import (
    list_directory_files,
    create_file_with_content,
    read_file_content,
    rename_file,
    delete_file
)

# 列出目录文件
result = list_directory_files("my_directory")
print(result)

# 创建文件
result = create_file_with_content("my_directory", "test.txt", "Hello World")

# 读取文件
result = read_file_content("my_directory", "test.txt")

# 重命名文件
result = rename_file("my_directory", "test.txt", "renamed.txt")

# 删除文件
result = delete_file("my_directory", "renamed.txt")
```

### 3. 网络访问工具 (practice01/network_operations.py)

提供HTTP请求访问网页的功能，类似curl命令。

#### 功能列表

1. **curl_webpage(url, method, headers, params, data, json_data, timeout, follow_redirects)**
   - 核心网络访问函数
   - 支持多种HTTP方法（GET、POST、PUT、DELETE等）
   - 自动处理不同类型的内容（JSON、文本、二进制）
   - 完善的错误处理和超时控制

2. **curl_get(url, **kwargs)**
   - GET请求便捷方法
   - 快速获取网页内容

3. **curl_post(url, **kwargs)**
   - POST请求便捷方法
   - 支持发送JSON数据和表单数据

**使用示例：**

```python
from practice01.network_operations import curl_get, curl_post, curl_webpage

# GET请求
result = curl_get("https://www.example.com")
print(f"状态码: {result['status_code']}")
print(f"内容: {result['content']}")

# 获取JSON数据
result = curl_get("https://api.example.com/data")
if result['success'] and result['content_type_category'] == 'json':
    data = result['content']
    print(data)

# POST请求
result = curl_post(
    "https://api.example.com/submit",
    json_data={"name": "测试", "value": 123}
)

# 自定义请求
result = curl_webpage(
    url="https://api.example.com/data",
    method="PUT",
    headers={"Authorization": "Bearer token"},
    json_data={"key": "value"},
    timeout=60
)
```

**返回数据结构：**

```json
{
  "success": true,
  "url": "https://example.com",
  "method": "GET",
  "status_code": 200,
  "status_reason": "OK",
  "elapsed_time": 0.234,
  "headers": {...},
  "content_length": 1234,
  "content_type": "text/html",
  "encoding": "utf-8",
  "content_type_category": "text",
  "content": "...",
  "content_preview": "...",
  "final_url": "https://example.com",
  "redirect_history": []
}
```

### 4. AnythingLLM集成模块 (practice04/)

提供与AnythingLLM的集成功能，支持查询文档仓库。

#### 4.1 AnythingLLM客户端 (anythingllm_client.py)

**核心功能：**

1. **anythingllm_query**
   - 使用subprocess模块调用curl命令访问AnythingLLM API
   - 支持通过message字段发送查询
   - 使用API密钥进行认证
   - 错误处理和异常捕获
   - 中文编码支持

**使用方法：**

```bash
# 测试AnythingLLM连接
python practice04/anythingllm_client.py
```

**环境变量配置：**

在 `.env` 文件中添加：
```
ANYTHINGLLM_API_KEY=1EQRFAH-NPGMMM7-PHT476X-3848R2Q
ANYTHINGLLM_WORKSPACE_SLUG=mywork
ANYTHINGLLM_BASE_URL=http://localhost:3001
```

**技术特点：**

- 使用subprocess模块调用curl命令
- 支持API密钥认证
- 完善的错误处理机制
- UTF-8编码支持，解决中文编码问题
- 动态配置API URL和工作区slug

#### 4.2 工具调用客户端 (tool_client.py)

**功能特性：**

- 集成AnythingLLM查询工具
- 支持文件操作、网络访问、聊天历史搜索和文档仓库查询
- 自动触发工具调用
- 实时显示工具调用过程和结果

**使用方法：**

```bash
# 启动工具调用客户端
python practice04/tool_client.py
```

**操作示例：**

```
# 正常聊天
你: 你好
助手: 你好！我是一个AI助手，有什么我可以帮助你的吗？

# 查询文档仓库
你: 文档仓库中有什么内容？
执行工具: anythingllm_query
参数: {'message': '文档仓库中有什么内容？'}
工具执行结果: {"success": true, "content": "根据文档仓库中的信息，仓库中包含了项目文档、API文档和用户指南等内容。"}
助手: 根据文档仓库中的信息，仓库中包含了项目文档、API文档和用户指南等内容。
```

**可用工具：**

- list_directory: 列出目录内容
- rename_file: 重命名文件
- delete_file: 删除文件
- create_file: 创建文件
- read_file: 读取文件
- fetch_webpage: 访问网页
- search_chat_history: 搜索聊天历史
- anythingllm_query: 查询文档仓库

**智能触发：**

- 当用户提到"文档仓库"、"文件仓库"、"仓库"时自动触发anythingllm_query工具
- 当用户输入以'/search'开头或表达'查找聊天历史'的意思时自动触发search_chat_history工具

## 安装依赖

```bash
pip install requests python-dotenv
```

## 运行示例

### 文件操作示例

```bash
cd practice01
python file_operations.py
python example_usage.py
```

### 网络访问示例

```bash
cd practice01
python network_operations.py
```

或从主目录运行：

```bash
python main.py --network
```

## 特性

- **模块化设计**: 文件操作和网络访问功能分离，便于维护
- **完善的错误处理**: 所有函数都包含详细的错误处理和返回信息
- **类型提示**: 使用Python类型提示，提高代码可读性
- **UTF-8编码**: 文件操作统一使用UTF-8编码
- **超时控制**: 网络请求支持超时设置，避免长时间等待
- **内容类型自动识别**: 自动识别JSON、文本、二进制内容
- **AnythingLLM集成**: 支持查询文档仓库的智能助手

## AnythingLLM集成

### 功能介绍

主程序支持与AnythingLLM的集成，当用户提到"文档仓库"、"文件仓库"、"仓库"等关键词时，会自动调用AnythingLLM API进行查询。

### 配置方法

1. 在 `.env` 文件中添加AnythingLLM配置：
   ```
   ANYTHINGLLM_API_KEY=your_anythingllm_api_key
   ANYTHINGLLM_WORKSPACE_SLUG=mywork
   ANYTHINGLLM_BASE_URL=http://localhost:3001
   ```

2. 确保AnythingLLM服务运行在配置的BASE_URL

3. API端点：`{BASE_URL}/api/v1/workspace/{WORKSPACE_SLUG}/chat`

### 使用示例

```bash
# 测试AnythingLLM连接
python main.py --test-anythingllm

# 启动聊天（支持自动触发AnythingLLM查询）
python main.py
```

**聊天示例：**

```
你: 文档仓库中有什么内容？
[工具调用] anythingllm_query: 文档仓库中有什么内容？
助手: 根据文档仓库中的信息，仓库中包含了项目文档、API文档和用户指南等内容。
```

### 技术实现

- 使用 `subprocess` 模块调用 `curl` 命令访问AnythingLLM API
- 支持API密钥认证和错误处理
- 与LLM的function call功能集成
- 实时显示工具调用过程和结果
- 支持中文编码和动态API URL配置

## 开发说明

### 添加新功能

1. 在 `practice01/` 目录下创建新的模块文件
2. 在 `main.py` 中添加演示函数
3. 更新 README.md 文档

### 代码规范

- 使用类型提示
- 函数返回统一的字典结构，包含 `success` 字段
- 提供详细的错误信息
- 使用UTF-8编码

## 许可证

MIT License
=======
# git-test
>>>>>>> 5501235 (Initial commit)
