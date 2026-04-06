# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 快速开始

### 安装和运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置 API 密钥
export ANTHROPIC_API_KEY='your-api-key'
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
# 或创建 .env 文件

# 运行 CLI
dev-agent interactive         # 交互模式
dev-agent run "项目描述"       # 运行工作流
dev-agent --help              # 查看帮助
```

### 常用命令

```bash
# 测试
pytest tests/                          # 运行所有测试
pytest tests/test_xxx.py               # 运行单个测试文件
pytest tests/ --cov=src                # 带覆盖率

# 代码质量
ruff format src/ tests/                # 格式化代码
ruff check src/ tests/                 # 检查代码

# 运行组件
python -m src.cli.main interactive     # CLI 交互模式
python -m uvicorn src.api.main:app     # API 服务器 (阶段 3)

# Observer 工具 (实时监控 Agent 执行)
dev-agent watch                        # 一键启动 Observer（服务器 + 客户端）
dev-agent observer                     # 仅启动客户端
dev-agent observer-server              # 仅启动服务器
dev-agent replay                       # 回放历史会话
dev-agent run --observe "需求"         # 运行工作流并实时监控
dev-agent interactive --observe        # 交互模式启用观察
```

---

## 架构概览

### 整体架构

```
┌─────────────────────────────────────────────┐
│              CLI / API / Web UI             │
│           (入口层：用户交互界面)              │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│                Agent 层                      │
│  ┌─────────────────────────────────────┐    │
│  │  Agent (agent.py)                   │    │
│  │  - 基于 Claude API                   │    │
│  │  - 管理消息历史 (MessageHistory)     │    │
│  │  - 工具调用循环 (_agent_loop)        │    │
│  └─────────────────────────────────────┘    │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│               Tool 层                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Built-in│ │ Custom  │ │   MCP   │       │
│  │ think,  │ │ git,    │ │ servers │       │
│  │ file_*  │ │ shell,  │ │ (可选)  │       │
│  │         │ │ project │ │         │       │
│  └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────────────────────────────┘
```

### 核心组件

| 模块 | 路径 | 说明 |
|------|------|------|
| **Agent** | `src/agents/agent.py` | 核心 Agent 类，基于 Claude API，管理工具调用循环 |
| **Tools** | `src/agents/tools/` | 内置工具 (think, file_read, file_write, mcp) |
| **Custom Tools** | `src/tools/` | 自定义工具 (git, shell, project) |
| **CLI** | `src/cli/main.py` | Click 命令行入口 |
| **Observers** | `src/observers/` | Observer 工具 (Hook, Logger, Server, Client) |
| **Utils** | `src/utils/` | 配置管理、日志工具 |

### 数据流

```
用户请求 → CLI → Agent.run_async() → _agent_loop()
                                      │
                                      ▼
                          ┌──────────────────────┐
                          │  Claude API 调用      │
                          │  (带工具定义)         │
                          └──────────────────────┘
                                      │
                          ┌───────────┴──────────┐
                          │ 有 tool_use?         │
                          │ 是 → execute_tools() │
                          │ 否 → 返回响应         │
                          └──────────────────────┘
```

---

## 代码结构

```
dev-agent/
├── src/
│   ├── agents/            # Agent 核心模块 (从 quickstarts 复用)
│   │   ├── agent.py       # Agent 主类
│   │   ├── tools/         # 内置工具
│   │   │   ├── base.py    # Tool 基类
│   │   │   ├── think.py   # 思考工具
│   │   │   ├── file_tools.py
│   │   │   └── mcp_tool.py
│   │   └── utils/         # 工具函数
│   │       ├── history_util.py   # 消息历史管理
│   │       ├── tool_util.py      # 工具执行
│   │       └── connections.py    # MCP 连接
│   │
│   ├── tools/             # 自定义工具
│   │   ├── git_tool.py    # Git 操作
│   │   ├── shell_tool.py  # Shell 命令
│   │   └── project_tool.py# 项目生成
│   │
│   ├── cli/               # CLI 入口
│   │   └── main.py        # Click 命令定义
│   │
│   ├── api/               # REST API (阶段 3)
│   ├── core/              # 工作流引擎 (阶段 2)
│   └── utils/             # 通用工具
│       ├── config.py      # 配置管理
│       └── logging.py     # 日志配置
│
├── tests/                 # 测试 (与 src 平行结构)
├── design/                # 设计文档
├── examples/              # 示例脚本
└── storage/               # 运行时数据
```

---

## 开发规范速查

### 代码风格

| 项目 | 规范 |
|------|------|
| 命名 | 函数/变量：`snake_case`，类：`PascalCase` |
| 类型注解 | 公共 API 必须有类型注解 |
| Docstring | 中文，Google 风格 |
| 行宽 | 100 字符 |
| 格式化 | `ruff format` |
| Lint | `ruff check` |

### Docstring 模板

```python
async def execute(
    self,
    command: str,
    args: str = "",
) -> str:
    """执行命令

    Args:
        command: 命令类型
        args: 命令参数

    Returns:
        执行结果

    Raises:
        ErrorType: 错误条件
    """
```

### 测试规范

- 文件命名：`test_<模块名>.py`
- 类命名：`Test<类名>`
- 函数命名：`test_<功能>_<条件>_<结果>()`
- 覆盖率要求：核心模块 90%+, 整体 80%+

### 代码修改流程

**修改配置/默认值时的正确顺序：**

1. **搜索所有引用点** - 先用 Grep/Glob 找出代码、测试、文档中所有相关位置
2. **先更新测试** - 修改测试断言以反映新的预期行为
3. **再修改代码** - 修改实现代码
4. **最后更新文档** - 更新相关文档
5. **运行测试验证** - `pytest tests/` 确认所有测试通过

**错误示例（不要这样做）：**
- 先改代码再改测试
- 改完后不运行测试验证
- 跳过系统性搜索直接修改

**Git 提交前必须：**
- 运行 `pytest tests/` 确保测试通过
- 运行 `ruff check src/ tests/` 确保代码规范

### Git 提交

```
<类型>(<范围>): <主题>

类型：feat, fix, docs, style, refactor, test, chore
范围：agent, tool, engine, cli, api, docs
```

示例：`feat(tool): 添加 Git 工具`

---

## 阶段规划

| 阶段 | 状态 | 说明 |
|------|------|------|
| 阶段 1 | ✅ | 基础单 Agent 系统 (CLI + 工具) |
| 阶段 2 | ⏳ | 多 Agent 协作 (工作流引擎 + 上下文管理) |
| 阶段 3 | ⏳ | 生产系统 (Web UI + REST API + 监控) |

详细设计文档：`design/DESIGN.md`, `design/PHASE1.md`

---

## 关键实现细节

### Agent 类 (`src/agents/agent.py`)

- **核心方法**: `run_async(user_input)` - 异步运行 Agent
- **工具循环**: `_agent_loop()` - 持续处理直到无工具调用
- **消息历史**: `MessageHistory` 管理对话上下文，支持自动截断
- **MCP 支持**: 通过 `AsyncExitStack` 管理 MCP 连接生命周期
- **Observer Hook**: `observer_hook` 参数用于实时事件推送

### Tool 基类 (`src/agents/tools/base.py`)

```python
class Tool:
    def __init__(self, name: str, description: str, input_schema: dict):
        ...

    async def execute(self, **kwargs) -> str:
        """执行工具并返回结果字符串"""

    def to_dict(self) -> dict:
        """转换为 Claude API 格式"""
```

### 消息历史 (`src/agents/utils/history_util.py`)

- 管理用户/助手对话历史
- 自动截断超出上下文窗口的消息
- 跟踪 token 使用量

### Observer 系统 (`src/observers/`)

- **ObserverHook**: 事件回调分发，捕获 Agent 执行中的所有事件
- **JSONLogger**: 会话日志持久化到 `storage/logs/<session_id>.json`
- **ObserverServer**: WebSocket 服务器 (默认端口 8765) 广播事件
- **ObserverClient**: Rich TUI 客户端，实时显示事件

事件流程：
```
Agent → ObserverHook → JSONLogger (存储)
                   → WebSocket Server → ObserverClient (TUI 显示)
```

---

## 调试技巧

1. **启用详细日志**: Agent 初始化时设置 `verbose=True`
2. **查看工具调用**: 日志显示 `Tool call: <name>(<params>)`
3. **检查 token 使用**: `response.usage` 包含输入/输出 token 统计
4. **测试单个工具**: `pytest tests/tools/test_xxx.py -v`
5. **使用 Observer**: `dev-agent watch` 实时查看 Agent 执行过程
6. **回放历史**: `dev-agent replay` 查看历史会话日志
