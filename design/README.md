# DevAgent 设计文档索引

> 所有设计文档的导航中心
>
> 版本：1.0
>
> 更新日期：2026-04-05

---

## 文档结构

```
design/
├── README.md              # 本文档 - 文档索引
├── index.html             # 可视化设计文档（网页版）
│
├── DESIGN.md              # 总体设计文档
├── DEVELOPMENT_GUIDELINES.md  # 开发规范
├── PHASE1.md              # 阶段 1 实施指南
├── PHASE2.md              # 阶段 2 实施指南
└── PHASE3.md              # 阶段 3 实施指南
```

---

## 文档导航

### 📋 总体设计文档

| 文档 | 说明 | 阅读 |
|------|------|------|
| **DESIGN.md** | 项目概述、架构图、核心组件设计 | [阅读](./DESIGN.md) |
| **DEVELOPMENT_GUIDELINES.md** | 代码风格、测试、文档、Git 提交规范 | [阅读](./DEVELOPMENT_GUIDELINES.md) |
| **index.html** | 可视化设计文档（浏览器打开） | [打开](./index.html) |

### 📅 阶段实施文档

| 文档 | 时间 | 目标 | 阅读 |
|------|------|------|------|
| **PHASE1.md** | 2-4 周 | 基础单 Agent 系统 | [阅读](./PHASE1.md) |
| **PHASE2.md** | 4-8 周 | 多 Agent 协作系统 | [阅读](./PHASE2.md) |
| **PHASE3.md** | 8-12 周 | 完备生产系统 | [阅读](./PHASE3.md) |

---

## 快速导航

### 按角色

| 角色 | 推荐文档 |
|------|----------|
| **初学者** | DESIGN.md → PHASE1.md |
| **开发者** | PHASE1.md → PHASE2.md → PHASE3.md |
| **架构师** | DESIGN.md → PHASE2.md |
| **项目经理** | DESIGN.md（阶段规划部分） |

### 按主题

| 主题 | 相关文档 |
|------|----------|
| **架构设计** | DESIGN.md 第 2 章 |
| **Agent 实现** | PHASE2.md 第 6 章 |
| **工具开发** | PHASE1.md 第 6 章 |
| **工作流引擎** | PHASE2.md 第 4 章 |
| **CLI/Web/API** | PHASE3.md 第 2-4 章 |

---

## 文档摘要

### DESIGN.md - 总体设计

**内容概览**：
- 项目目标和设计原则
- 四层架构图
- 核心组件说明
- 三阶段演进规划
- 快速开始指南

**适合人群**：所有人

---

### PHASE1.md - 基础单 Agent 系统

**内容概览**：
- 环境准备和项目初始化
- 从 quickstarts 复制 agents 模块
- 创建自定义工具（Git、Shell、项目生成）
- 实现 CLI 命令行界面
- 创建示例脚本和文档

**代码示例**：
- GitTool 实现
- ShellTool 实现
- ProjectTool 实现
- cli.py 入口

**适合人群**：初学者、开发者

---

### PHASE2.md - 多 Agent 协作系统

**内容概览**：
- 工作流上下文设计
- 上下文存储实现
- 检查点管理
- 工作流引擎实现
- 5 个专用 Agent 实现

**代码示例**：
- WorkflowContext 类
- ContextStore 类
- CheckpointManager 类
- WorkflowEngine 类
- BaseAgent 基类
- RequirementsAgent
- DesignAgent
- CodingAgent
- TestingAgent
- DeliveryAgent

**适合人群**：开发者、架构师

---

### PHASE3.md - 完备生产系统

**内容概览**：
- CLI TUI 界面实现
- Web 可视化界面（Next.js）
- REST API（FastAPI）
- 日志系统
- 测试套件
- 完整文档

**代码示例**：
- CLI 主程序（click + rich）
- Web 页面（React/Next.js）
- REST API（FastAPI）
- 日志配置
- 单元测试

**适合人群**：高级开发者

---

## 检查清单

### 阶段 1 检查清单

- [x] 环境准备完成
- [x] 项目结构创建
- [x] agents 模块复制
- [x] GitTool 创建并测试
- [x] ShellTool 创建并测试
- [x] CLI 入口创建并运行
- [x] 示例脚本创建
- [x] README.md 创建
- [x] 开发规范制定
- [x] 单元测试编写

### 阶段 2 检查清单

- [ ] WorkflowContext 创建
- [ ] ContextStore 创建
- [ ] CheckpointManager 创建
- [ ] WorkflowEngine 创建
- [ ] BaseAgent 创建
- [ ] 5 个专用 Agent 实现
- [ ] 完整工作流测试

### 阶段 3 检查清单

- [ ] CLI TUI 完成
- [ ] Web UI 完成
- [ ] REST API 完成
- [ ] 日志系统完成
- [ ] 测试套件完成
- [ ] 完整文档编写

---

## 外部资源

| 资源 | 链接 |
|------|------|
| Claude API 文档 | https://docs.claude.com |
| claude-quickstarts | https://github.com/anthropics/claude-quickstarts |
| Anthropic Discord | https://www.anthropic.com/discord |
| Rich 库文档 | https://rich.readthedocs.io |
| FastAPI 文档 | https://fastapi.tiangolo.com |
| Next.js 文档 | https://nextjs.org/docs |

---

## 文档历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-04-05 | 初始版本，拆分阶段文档 |

---

**下一步**：开始阅读 [DESIGN.md](./DESIGN.md) 了解总体设计，或直接进入 [PHASE1.md](./PHASE1.md) 开始实施。
