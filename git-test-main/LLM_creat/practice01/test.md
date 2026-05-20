# 测试文档 (Test Specification)

## 1. 测试策略
- **测试层级**：单元测试 → 集成测试 → 端到端（E2E）功能测试
- **测试框架**：`pytest` + `pytest-asyncio`
- **覆盖率目标**：核心模块（`model_client`, `memory_system`, `search_tool`, `agent_graph`）≥ 70%
- **模拟对象**：模型 API 响应、搜索 API 响应、记忆向量存储（使用临时内存数据库）

## 2. 测试环境
- Python 3.10+，安装 `pytest`, `pytest-asyncio`, `pytest-cov`
- 配置 `conftest.py` 提供 fixtures（mock 模型客户端、mock 搜索、临时记忆目录）
- CI 环境：GitHub Actions 或本地运行，无需 GPU（使用模拟模型）

## 3. 单元测试

### 3.1 配置模块 (`test_config.py`)
| 测试ID | 测试用例 | 预期结果 |
|--------|----------|----------|
| UT-CFG-01 | 加载有效的 `config.yaml` 文件 | 返回 Config 对象，各字段值正确 |
| UT-CFG-02 | 缺失配置文件时使用默认值 | 不抛出异常，默认值生效 |
| UT-CFG-03 | 环境变量覆盖配置文件 | 环境变量优先级更高 |

### 3.2 模型客户端 (`test_model_client.py`)
使用 `unittest.mock` 模拟 HTTP 请求。

| 测试ID | 测试用例 | 预期结果 |
|--------|----------|----------|
| UT-MC-01 | `generate_stream` 返回有效 token 生成器 | 能够异步迭代并获得非空字符串 |
| UT-MC-02 | `generate` 收集流式输出并返回完整字符串 | 完整字符串等于各 token 拼接 |
| UT-MC-03 | 模拟网络错误时抛出自定义异常 | `ModelConnectionError` 被抛出 |
| UT-MC-04 | 传递 tools 参数时消息格式正确（检查序列化） | 无异常，最终 promopt 包含工具描述 |

### 3.3 记忆系统 (`test_memory_system.py`)
使用内存向量存储（Chroma 的 `EphemeralClient`）进行隔离测试。

| 测试ID | 测试用例 | 预期结果 |
|--------|----------|----------|
| UT-MEM-01 | `add_memory` 存储一条对话 | 存储后搜索能检索到相关内容 |
| UT-MEM-02 | `search_memory` 返回与查询语义相关的记忆 | 返回的记忆内容与查询匹配（相似度 > 0.7） |
| UT-MEM-03 | `delete_memory` 删除后不再出现在搜索结果中 | 删除后查询无该记忆 |
| UT-MEM-04 | 重复添加相似内容不产生过度冗余（Mem0 去重行为） | 同一事实只存储一次或合并 |

### 3.4 搜索工具 (`test_search_tool.py`)
模拟 `duckduckgo_search` 返回固定结果。

| 测试ID | 测试用例 | 预期结果 |
|--------|----------|----------|
| UT-SR-01 | `search` 正常返回结果列表 | 列表元素包含 title, snippet, url |
| UT-SR-02 | 模拟超时（延迟 > timeout） | 返回空列表，不抛出异常 |
| UT-SR-03 | 模拟 API 返回空结果 | 返回空列表 |
| UT-SR-04 | `format_search_results_as_context` 格式化输出 | 输出字符串包含标题和 URL，无空结果时输出“无搜索结果” |

### 3.5 工作流编排 (`test_agent_graph.py`)
独立测试各个节点函数和条件边逻辑，使用模拟的模型客户端和搜索工具。

| 测试ID | 测试用例 | 预期结果 |
|--------|----------|----------|
| UT-AG-01 | `retrieve_memory` 节点：给定用户消息，调用 `memory_sys.search_memory` | `state["memory_context"]` 被填充 |
| UT-AG-02 | `decide_action` 节点：模型返回 `{"action": "search", "query": "..."}` | `state["next_action"]` = "search"， `search_query` 正确 |
| UT-AG-03 | `decide_action` 节点：模型返回 `{"action": "respond"}` | `state["next_action"]` = "respond" |
| UT-AG-04 | `execute_search` 节点：`search_enabled` = True 且 `search_query` 存在 | 调用搜索工具，结果存入 `state["search_results"]` |
| UT-AG-05 | `execute_search` 节点：`search_enabled` = False | 不调用搜索，`search_results` 为空，`next_action` 设为 "respond" |
| UT-AG-06 | `generate_response` 节点：调用模型生成，并将回复追加到 messages | `state["messages"]` 最后一条 role 为 "assistant" |
| UT-AG-07 | 条件边：`next_action` = "search" → 路由至 execute_search | 图执行路径正确 |
| UT-AG-08 | 条件边：`next_action` = "respond" → 路由至 generate_response | 图执行路径正确 |

## 4. 集成测试

### 4.1 工作流端到端（模拟外部依赖）
使用真实的 LangGraph 图，但模型客户端和搜索引擎使用模拟（返回预设响应）。

| 测试ID | 测试场景 | 步骤 | 预期结果 |
|--------|----------|------|----------|
| IT-01 | 简单对话（无需记忆/搜索） | 用户输入“你好” | 最终回复非空，不调用搜索工具 |
| IT-02 | 需要搜索的问题 | 用户输入“今天天气”且 `search_enabled=True` | `decide_action` → search → 回复中包含搜索结果信息 |
| IT-03 | 搜索开关关闭 | 同上但 `search_enabled=False` | `decide_action` 直接 respond，不进入搜索节点 |
| IT-04 | 长期记忆检索 | 第一轮：用户说“我是张三”；第二轮：询问“我叫什么” | 第二轮能检索到记忆并回答“张三” |
| IT-05 | 记忆更新 | 用户先说“我喜欢咖啡”，后说“我其实喜欢茶” | 后续查询“我喜欢什么”回答“茶”（覆盖旧记忆） |
| IT-06 | 搜索超时降级 | 模拟搜索超时 | 回复中不包含搜索结果，且提示“当前无法联网” |
| IT-07 | 复杂任务规划 | 用户：“对比昨天和今天的金价” | Agent 执行两次搜索（昨日、今日），最后给出对比结论 |

### 4.2 终端界面集成 (`test_cli.py`)
模拟用户输入，捕获 stdout 输出。

| 测试ID | 测试用例 | 预期结果 |
|--------|----------|----------|
| IT-CLI-01 | 输入普通文本消息 | 程序输出 `Agent >` 开头的内容 |
| IT-CLI-02 | 输入 `/clear` 命令 | 清空对话上下文，后续问题不记得之前对话 |
| IT-CLI-03 | 输入 `/memory` | 显示已存储的记忆列表（如果有） |
| IT-CLI-04 | 输入 `/search off` 后联网问题 | Agent 不再调用搜索工具 |
| IT-CLI-05 | 输入 `exit` | 程序正常退出，无异常 |

## 5. 端到端功能测试 (E2E)

在有 GPU 或 CPU 的完整环境中运行真实模型（Qwen3.4-4b）和真实搜索 API，手动或自动执行关键场景。

| 测试ID | 测试场景 | 验收标准 |
|--------|----------|----------|
| E2E-01 | 启动程序到首次对话 | 程序启动无报错，输入“你好”能流式输出回复 |
| E2E-02 | 跨会话记忆 | 退出重启后，询问“你还记得我叫什么吗？”能正确回忆 |
| E2E-03 | 实时搜索 | 询问“最新电影《热辣滚烫》的票房”能返回包含数字的回答并引用来源 |
| E2E-04 | 拒绝搜索开关 | 关闭搜索后询问“今天新闻”，回复不包含实时信息且无搜索调用 |
| E2E-05 | 复杂任务 | 要求“计算 123*456 并告诉我步骤”，Agent 能通过计算工具（如果已实现）或自身推理给出正确结果 |
| E2E-06 | 错误处理 | 断开网络后询问需要搜索的问题，AI 提示无法联网并给出常规回答 |

## 6. 性能与压力测试

| 测试ID | 测试项 | 方法 | 通过标准 |
|--------|--------|------|----------|
| PT-01 | 首 token 延迟 | 测量从输入完成到第一个字符打印的时间（推荐 GPU） | ≤ 2 秒（95% 请求） |
| PT-02 | 生成速度 | 计算每秒生成的 token 数 | ≥ 20 token/秒 |
| PT-03 | 记忆检索延迟 | 测量 `search_memory` 调用耗时 | ≤ 500 ms（P95） |
| PT-04 | 搜索超时控制 | 模拟慢响应，观察是否 5 秒超时 | 实际请求时间 ≤ 5.5 秒 |
| PT-05 | 内存泄漏 | 连续运行 100 轮对话，监控内存占用 | 内存增长 ≤ 初始 20% |

## 7. 测试执行清单

### 7.1 运行所有单元测试
```bash
pytest tests/unit -v --cov=src --cov-report=term