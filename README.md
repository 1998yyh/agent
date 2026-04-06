# DevAgent

基于 claude-quickstarts 的多 Agent 软件开发系统。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置 API 密钥

```bash
export ANTHROPIC_API_KEY='your-api-key'
```

或创建 `.env` 文件：

```
ANTHROPIC_API_KEY=your-api-key
ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
```

**支持的模型**：`glm-5` (默认), `qwen3.5-plus`, `qwen3-max-2026-01-23`, `qwen3-coder-next`, `qwen3-coder-plus`, `glm-4.7`, `kimi-k2.5`, `MiniMax-M2.5`

```
# 可选：指定模型名称
ANTHROPIC_MODEL=glm-5
```

### 3. 运行 CLI

```bash
# 交互模式
python -m src.cli.main interactive

# 运行工作流
python -m src.cli.main run "创建一个 Python 计算器项目"

# 查看帮助
python -m src.cli.main --help
```

## 阶段 1 功能

- [x] 基础单 Agent 系统
- [x] CLI 命令行界面
- [x] 文件读写工具
- [x] Git 工具
- [x] Shell 工具
- [x] 项目生成工具

## 示例

```bash
# 运行基础对话示例
python examples/basic_chat.py

# 运行创建项目示例
python examples/create_project.py
```

## 目录结构

```
dev-agent/
├── src/                   # 源代码
│   ├── agents/            # Agent 模块
│   ├── tools/             # 工具模块
│   ├── cli/               # CLI 入口
│   └── utils/             # 工具函数
├── tests/                 # 测试目录
├── examples/              # 示例脚本
├── storage/               # 存储目录
├── design/                # 设计文档
├── requirements.txt       # 依赖
└── README.md              # 本文件
```

## 文档

- [总体设计](./design/DESIGN.md)
- [阶段 1 实施指南](./design/PHASE1.md)
- [阶段 2 实施指南](./design/PHASE2.md)
- [阶段 3 实施指南](./design/PHASE3.md)
- [开发规范](./CLAUDE.md)

## License

MIT
