# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 常用命令

```bash
# 安装
pip install -r requirements.txt

# 环境变量
export ANTHROPIC_API_KEY='your-api-key'
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic  # 阿里云百炼代理
export ANTHROPIC_MODEL=glm-5  # 可选，默认 glm-5

# CLI 命令 (入口: dev-agent, 通过 pyproject.toml [project.scripts] 注册)
dev-agent interactive                  # 交互模式 (单 Agent + 全部工具)
dev-agent interactive --observe        # 交互模式 + Observer 实时监控
dev-agent run "需求描述"               # 多 Agent 工作流 (5 阶段流水线)
dev-agent run --observe "需求描述"     # 工作流 + 实时监控
dev-agent workflow "需求描述"          # 同 run，功能一致
dev-agent resume <workflow_id>         # 从检查点恢复工作流
dev-agent list-workflows               # 列出最近工作流
dev-agent status <workflow_id>         # 显示工作流状态

# Observer 监控 (独立启动)
dev-agent watch                        # 一键启动 Observer（服务器 + 客户端）
dev-agent observer-server              # 仅启动 WebSocket 服务器 (默认 127.0.0.1:8765)
dev-agent observer                     # 仅启动 TUI 客户端
dev-agent replay [session_id]          # 回放历史会话日志

# 测试
pytest tests/                          # 全部测试
pytest tests/test_xxx.py               # 单个测试文件
pytest tests/test_xxx.py::TestClass::test_method -v  # 单个测试方法
pytest tests/ --cov=src                # 带覆盖率

# 代码质量
ruff format src/ tests/                # 格式化
ruff check src/ tests/                 # Lint 检查
```

---

## 架构概览

### 三层架构

```
┌──────────────────────────────────────────────────────┐
│                   CLI (src/cli/main.py)               │
│    Click 命令行 → interactive / run / workflow / ...  │
└───────────────────┬──────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐     ┌──────────────────────────────┐
│  单 Agent 模式 │     │      多 Agent 工作流模式       │
│ (interactive)  │     │ (run / workflow / resume)     │
│               │     │                              │
│  Agent 类      │     │  WorkflowEngine              │
│  (agents/     │     │  (orchestrator/)              │
│   agent.py)   │     │       │                      │
│               │     │  5 阶段 Agent 流水线:          │
│               │     │  Requirements → Design →      │
│               │     │  Coding → Testing → Delivery  │
│               │     │  (agents_custom/)             │
└───────┬───────┘     └──────────────┬───────────────┘
        │                            │
        └────────────┬───────────────┘
                     ▼
┌──────────────────────────────────────────────────────┐
│                    Tool 层                            │
│  框架工具 (agents/tools/):                            │
│    Think, FileRead, FileWrite, MCP                   │
│  业务工具 (tools/):                                   │
│    Git, Shell, Project                               │
└──────────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 路径 | 说明 |
|------|------|------|
| **Agent** | `src/agents/agent.py` | 核心 Agent，管理工具调用循环、消息历史、MCP 连接 |
| **AgentFactory** | `src/agents/factory.py` | 预设模型映射的工厂类，提供 `create_*_agent()` 方法 |
| **Custom Agents** | `src/agents_custom/` | 5 个专用 Agent (Requirements/Design/Coding/Testing/Delivery) |
| **WorkflowEngine** | `src/orchestrator/workflow_engine.py` | 多 Agent 流水线编排，顺序执行 5 个阶段 |
| **ContextStore** | `src/orchestrator/context_store.py` | 工作流上下文持久化 (`storage/workflows/`) |
| **CheckpointManager** | `src/orchestrator/checkpoint.py` | 断点续跑 (`storage/checkpoints/`) |
| **Observer** | `src/observers/` | 实时监控系统 (Hook → Logger + WebSocket → TUI) |
| **CLI** | `src/cli/main.py` | Click 命令行入口，注册 10+ 命令 |

### Agent 核心循环

`Agent.run_async()` → `_agent_loop()` 的循环逻辑:

1. 添加用户消息到 `MessageHistory`
2. 截断历史以适应上下文窗口 (`context_window_tokens` 默认 180000)
3. 调用 Claude API（同步 `client.messages.create()`，带 `anthropic-beta: code-execution-2025-05-22` 头）
4. 检查响应是否包含 `tool_use` → 执行工具 → 继续循环
5. 无工具调用时返回最终文本响应

### 多 Agent 工作流

`WorkflowEngine` 按顺序执行 5 个阶段，每个阶段由专用 Agent 处理:

| 阶段 | Agent | 角色 | 工具集 |
|------|-------|------|--------|
| requirements | RequirementsAgent | 需求分析 | Think |
| design | DesignAgent | 架构设计 | Think |
| coding | CodingAgent | 代码实现 | Think, FileRead, FileWrite, Git, Shell |
| testing | TestingAgent | 测试验证 | Think, FileRead, Shell |
| delivery | DeliveryAgent | 交付审查 | 无 (不调用 LLM) |

工作流数据通过 `WorkflowContext` 在阶段间传递，包含 `requirements_doc`, `design_doc`, `source_files`, `test_results`, `delivery_report` 等字段。

### Observer 事件流

```
Agent 执行
  │
  ▼
ObserverHook (hook.py) ── 注入到 Agent 构造函数
  │
  ├──→ JSONLogger (logger.py) → SessionLog (session.py) → storage/logs/<session_id>.json
  │
  └──→ WebSocketClient (server_client.py) → ObserverServer (server.py) → ObserverClient (client.py) [Rich TUI]
```

9 种事件类型 (`events.py`): `SESSION_START`, `USER_MESSAGE`, `AI_THINKING`, `TOOL_CALL`, `TOOL_RESULT`, `API_CALL`, `API_RESPONSE`, `AI_RESPONSE`, `SESSION_END`

### 工具系统

所有工具继承 `Tool` 基类 (`src/agents/tools/base.py`)，这是一个 **`@dataclass`**:

```python
@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict

    async def execute(self, **kwargs) -> str: ...
    def to_dict(self) -> dict: ...  # 转为 Claude API 工具格式
```

**框架工具** (`src/agents/tools/`): 使用 `asyncio.to_thread` 包装 IO 操作
**业务工具** (`src/tools/`): 使用 `subprocess.run` (同步)，但 `execute()` 仍为 async

---

## 配置与环境

### 模型配置 (`src/utils/config.py`)

`ModelConfig` 默认值:
- `model`: `"glm-5"` (通过百炼 API 代理，非真正 Claude 模型)
- `max_tokens`: 16000
- `context_window_tokens`: 180000
- `temperature`: 未设置

支持的模型 (通过百炼 API): `glm-5`, `qwen3.5-plus`, `qwen3-max-2026-01-23`, `qwen3-coder-next`, `qwen3-coder-plus`, `glm-4.7`, `kimi-k2.5`, `MiniMax-M2.5`

### 关键配置文件

| 文件 | 用途 |
|------|------|
| `pyproject.toml` | 项目元数据，Python >=3.8，入口点 `dev-agent` |
| `requirements.txt` | 依赖（含 websockets，pyproject.toml 中缺失该依赖） |
| `ruff.toml` | 行宽 100，目标 py38，启用 E/W/F/I/B/C4 规则 |
| `pytest.ini` | `asyncio_mode = auto`, `pythonpath = src` |
| `.env` / `.env.example` | API 密钥和基础 URL |

### import 路径

项目使用 `pythonpath = src`（pytest.ini）和 `sys.path.insert`（CLI）使得模块可直接导入。测试和代码中的 import 形如:
```python
from agents.agent import Agent
from utils.config import ModelConfig
from orchestrator.workflow_engine import WorkflowEngine
```

---

## 开发规范

### 代码风格

- 命名: `snake_case` (函数/变量), `PascalCase` (类)
- 公共 API 必须有类型注解
- Docstring: 中文，Google 风格
- 行宽: 100 字符
- 格式化/Lint: `ruff format` / `ruff check`

### 测试规范

- 异步测试自动处理 (`asyncio_mode = auto`)
- 文件: `test_<模块名>.py`，类: `Test<类名>`，函数: `test_<功能>_<条件>_<结果>()`
- 全局 fixtures 在 `tests/conftest.py`: `temp_dir` (临时目录), `api_key` (mock key)
- 覆盖率要求: 核心模块 90%+, 整体 80%+

### 代码修改流程

1. **搜索所有引用点** - 先用 Grep/Glob 找出代码、测试、文档中所有相关位置
2. **先更新测试** - 修改测试断言以反映新的预期行为
3. **再修改代码** - 修改实现代码
4. **最后更新文档** - 更新相关文档
5. **运行测试验证** - `pytest tests/` 确认所有测试通过

### Git 提交格式

```
<类型>(<范围>): <主题>

类型: feat, fix, docs, style, refactor, test, chore
范围: agent, tool, engine, cli, api, observer, docs
```

提交前必须: `pytest tests/` + `ruff check src/ tests/`

---

## 阶段规划

| 阶段 | 状态 | 说明 |
|------|------|------|
| 阶段 1 | ✅ | 基础单 Agent 系统 (CLI + 工具) |
| 阶段 2 | ⏳ | 多 Agent 协作 (工作流引擎 + 上下文管理) -- agents_custom/ 和 orchestrator/ 已有基础实现 |
| 阶段 3 | ⏳ | 生产系统 (Web UI + REST API + 监控) -- api/ 和 core/ 目前为空占位 |

设计文档: `design/DESIGN.md`, `design/PHASE1.md`, `design/PHASE2.md`, `design/PHASE3.md`, `design/OBSERVER.md`

---

## 调试技巧

1. **详细日志**: Agent 初始化时 `verbose=True`
2. **工具调用日志**: 输出 `Tool call: <name>(<params>)`
3. **token 统计**: `response.usage` 包含输入/输出 token
4. **单个工具测试**: `pytest tests/tools/test_xxx.py -v`
5. **实时监控**: `dev-agent watch` 实时查看 Agent 执行
6. **回放历史**: `dev-agent replay` 查看历史会话
7. **工作流断点**: 使用 `dev-agent resume <workflow_id>` 从失败点恢复
