# Observer 工具使用指南

> 实时查看 Agent 交互过程的观察者工具
>
> 版本：1.0
>
> 创建日期：2026-04-06

---

## 1. 概述

Observer 工具允许用户实时查看 Agent 的完整交互过程，包括：
- 用户提问
- AI 思考过程（think 工具内容）
- 工具调用和结果
- API 调用详情（模型、token 使用）
- AI 最终回答

同时自动保存日志到 JSON 文件，支持历史回放。

---

## 2. 快速开始

### 2.1 安装依赖

```bash
pip install -r requirements.txt
```

### 2.2 一键启动（推荐）

最简单的方式，自动启动服务器和客户端：

```bash
dev-agent watch
```

然后在另一个终端窗口运行：

```bash
dev-agent interactive --observe
# 或
dev-agent run --observe "创建一个 Python 项目"
```

### 2.3 分步启动（高级）

如果需要更多控制权，可以分别启动服务器和客户端：

```bash
# 终端 1：启动服务器
dev-agent observer-server

# 终端 2：启动客户端
dev-agent observer

# 终端 3：运行带观察的 Agent
dev-agent interactive --observe
```

### 2.4 停止观察

按 `Ctrl+C` 断开 Observer 客户端连接。

---

## 3. 功能说明

### 3.1 TUI 界面布局

```
╭─────────────────────────────────────────────────────────────╮
│  DevAgent Observer | Session: 20260406_143022_abc123        │
├─────────────────────────────────────────────────────────────┤
│ [用户提问] 14:30:25                                         │
│ 创建一个 Python 计算器项目                                   │
├─────────────────────────────────────────────────────────────┤
│ [AI 思考] 14:30:28                                          │
│ 我需要先创建项目结构，然后编写计算器代码...                  │
├─────────────────────────────────────────────────────────────┤
│ [AI 回答] 14:30:35                                          │
│ 项目已创建完成！包含以下文件：                               │
│ - calculator.py (计算器主程序)                               │
│ - README.md (项目说明)                                      │
├─────────────────────────────────────────────────────────────┤
│ [事件日志]                                                   │
│ [14:30:25] USER_MESSAGE                                     │
│ [14:30:28] AI_THINKING                                      │
│ [14:30:30] TOOL_CALL: file_write                            │
│ [14:30:32] TOOL_RESULT                                      │
│ [14:30:35] AI_RESPONSE                                      │
╰─────────────────────────────────────────────────────────────╯
```

### 3.2 日志文件

日志保存在 `storage/logs/<session_id>.json`

示例结构：
```json
{
  "session_id": "20260406_143022_abc123",
  "start_time": "2026-04-06T14:30:22",
  "end_time": "2026-04-06T14:35:10",
  "metadata": {"model": "glm-5"},
  "events": [
    {
      "type": "user_message",
      "timestamp": "2026-04-06T14:30:25",
      "data": {"content": "创建一个 Python 计算器项目"}
    },
    {
      "type": "ai_thinking",
      "timestamp": "2026-04-06T14:30:28",
      "data": {"content": "我需要先创建项目结构..."}
    }
  ]
}
```

---

## 4. CLI 命令参考

### 4.1 observer-server

启动 Observer WebSocket 服务器。

```bash
dev-agent observer-server [OPTIONS]

Options:
  -p, --port INTEGER    服务器端口 (默认：8765)
  -h, --host TEXT       监听地址 (默认：127.0.0.1)
  --help                显示帮助
```

### 4.2 observer

启动 Observer 客户端，连接到服务器并显示 TUI 界面。

```bash
dev-agent observer [OPTIONS]

Options:
  -s, --server TEXT     Observer 服务器地址 (默认：ws://127.0.0.1:8765)
  --help                显示帮助
```

### 4.3 replay

回放历史会话。

```bash
dev-agent replay [SESSION_ID]

Arguments:
  SESSION_ID    会话 ID（可选，不提供则列出所有会话）

Options:
  --help        显示帮助
```

示例：
```bash
# 列出所有会话
dev-agent replay

# 回放指定会话
dev-agent replay 20260406_143022_abc123
```

### 4.4 run

运行工作流，支持 `--observe` 标志启用观察。

```bash
dev-agent run [OPTIONS] REQUEST

Options:
  -o, --observe       启用 Observer 实时观察
  -v, --verbose       启用详细输出
  -m, --model TEXT    指定模型名称
  -b, --base-url TEXT 指定 API 基础地址
```

### 4.5 interactive

进入交互模式，支持 `--observe` 标志启用观察。

```bash
dev-agent interactive [OPTIONS]

Options:
  -o, --observe       启用 Observer 实时观察
  -m, --model TEXT    指定模型名称
  -b, --base-url TEXT 指定 API 基础地址
```

---

## 5. 事件类型

Observer 工具捕获以下事件类型：

| 事件类型 | 说明 |
|----------|------|
| `session_start` | 会话开始，包含模型名称和工具列表 |
| `user_message` | 用户提问内容 |
| `ai_thinking` | AI 思考过程（think 工具内容） |
| `tool_call` | 工具调用开始，包含工具名称和参数 |
| `tool_result` | 工具执行结果 |
| `api_call` | Claude API 调用，包含模型和参数 |
| `api_response` | API 响应，包含 token 使用统计 |
| `ai_response` | AI 最终回答 |
| `session_end` | 会话结束，包含总 token 数和持续时间 |

---

## 6. 常见问题

### Q: 无法连接到 Observer 服务器

**A:** 确保服务器已启动：
```bash
dev-agent observer-server
```

### Q: 日志文件在哪里？

**A:** 日志文件保存在 `storage/logs/` 目录下，以会话 ID 命名。

### Q: 如何查看历史会话列表？

**A:** 运行以下命令：
```bash
dev-agent replay
```

### Q: Observer 服务器可以远程访问吗？

**A:** 可以。使用 `--host 0.0.0.0` 启动服务器：
```bash
dev-agent observer-server --host 0.0.0.0 --port 8765
```

然后从其他机器连接：
```bash
dev-agent observer --server ws://<服务器 IP>:8765
```

---

## 7. 架构说明

Observer 系统由以下组件组成：

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI (主进程)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │    Agent     │→│ ObserverHook │→│  JSON Logger     │  │
│  │  (事件触发)  │  │  (回调分发)  │  │  (存储到文件)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         │                                                   │
│         │ WebSocket                                         │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Observer Server (后台)                  │   │
│  │         - 接收事件                                    │   │
│  │         - 广播给连接的客户端                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ WebSocket
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              Observer CLI (独立进程)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Rich TUI 界面                                       │  │
│  │   - 用户提问面板                                      │  │
│  │   - AI 思考过程面板                                   │  │
│  │   - 工具调用面板                                      │  │
│  │   - AI 回答面板                                       │  │
│  │   - 事件日志面板                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. 下一步

- Web 可视化仪表板（阶段 3）
- 多会话对比
- 事件过滤和搜索
- 导出为 HTML 报告

---

*设计文档：`design/OBSERVER.md`*
*实施计划：`docs/superpowers/plans/2026-04-06-observer-tool.md`*
