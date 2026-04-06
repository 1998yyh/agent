# DevAgent 后端项目

> 多 Agent 协作的软件开发系统

---

## 阶段完成状态

| 阶段 | 状态 | 说明 |
|------|------|------|
| 阶段 1 | ✅ 完成 | 基础单 Agent 系统 (CLI + 工具) |
| 阶段 2 | ✅ 完成 | 多 Agent 协作系统 (工作流引擎 + 5 个专用 Agent) |
| 阶段 3 | ⏳ 待开始 | 生产系统 (REST API + Web UI) |

---

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 设置环境变量

```bash
export ANTHROPIC_API_KEY='your-api-key'
export ANTHROPIC_BASE_URL='https://coding.dashscope.aliyuncs.com/apps/anthropic'
```

### 运行

```bash
# 运行多 Agent 工作流
dev-agent workflow "创建一个 Python 计算器项目"

# 交互模式
dev-agent interactive

# 查看帮助
dev-agent --help
```

---

## 项目结构

```
dev-agent/
├── src/
│   ├── agents/              # Agent 核心模块 (阶段 1)
│   │   ├── agent.py
│   │   ├── tools/
│   │   └── utils/
│   ├── agents_custom/       # 5 个专用 Agent (阶段 2)
│   │   ├── base.py
│   │   ├── requirements.py
│   │   ├── design.py
│   │   ├── coding.py
│   │   ├── testing.py
│   │   └── delivery.py
│   ├── orchestrator/        # 工作流编排层 (阶段 2)
│   │   ├── workflow_engine.py
│   │   ├── context_store.py
│   │   └── checkpoint.py
│   ├── tools/               # 自定义工具
│   │   ├── git_tool.py
│   │   ├── shell_tool.py
│   │   └── project_tool.py
│   ├── observers/           # Observer 系统
│   │   ├── hook.py
│   │   ├── logger.py
│   │   ├── server.py
│   │   └── client.py
│   ├── cli/
│   │   └── main.py
│   └── utils/
├── tests/
└── requirements.txt
```

---

## CLI 命令

| 命令 | 说明 |
|------|------|
| `dev-agent workflow <需求>` | 运行多 Agent 工作流 |
| `dev-agent resume <workflow_id>` | 从检查点恢复 |
| `dev-agent list-workflows` | 列出工作流 |
| `dev-agent status <workflow_id>` | 查看状态 |
| `dev-agent interactive` | 交互模式 |
| `dev-agent run <需求>` | 运行单 Agent 任务 |
| `dev-agent watch` | 一键启动 Observer |
| `dev-agent observer` | 启动 Observer 客户端 |
| `dev-agent observer-server` | 启动 Observer 服务器 |
| `dev-agent replay` | 回放历史会话 |

---

## 工作流阶段

```
用户需求
    ↓
┌─────────────────┐
│ RequirementsAgent │ ← 需求分析
└────────┬────────┘
         ↓
┌─────────────────┐
│   DesignAgent    │ ← 技术方案
└────────┬────────┘
         ↓
┌─────────────────┐
│   CodingAgent    │ ← AI 编码
└────────┬────────┘
         ↓
┌─────────────────┐
│  TestingAgent    │ ← 测试生成
└────────┬────────┘
         ↓
┌─────────────────┐
│  DeliveryAgent   │ ← 交付审查
└─────────────────┘
```

---

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行单个测试文件
pytest tests/orchestrator/test_checkpoint.py -v

# 带覆盖率
pytest tests/ --cov=src
```

---

## 后续工作

### REST API (阶段 3)
- [ ] FastAPI 应用
- [ ] 工作流管理端点
- [ ] 阶段对话端点
- [ ] WebSocket 实时推送

### 前端集成
- [ ] 前后端 API 对接
- [ ] 实时事件订阅
- [ ] 代码编辑器

---

## License

MIT
