# 阶段 1 实施指南：基础单 Agent 系统

> **时间**: 2-4 周
>
> **目标**: 理解 Agent 基础架构，能运行简单开发任务

---

## 1. 阶段 1 概述

### 1.1 目标

完成阶段 1 后，你将能够：
- 理解 Agent 基础架构和 Tool Use 机制
- 创建和使用自定义工具
- 通过 CLI 与 Agent 对话
- 使用 Agent 创建简单项目

### 1.2 交付物

| 交付物 | 说明 |
|--------|------|
| 可运行的 CLI Agent | 命令行界面，可与 Agent 交互 |
| 5+ 自定义工具 | Git、Shell、项目生成等工具 |
| 示例脚本集 | 演示各种用法的示例代码 |
| 基础文档 | README 和使用说明 |

### 1.3 时间规划

| 任务 | 预计时间 |
|------|----------|
| 环境准备和项目初始化 | 1-2 天 |
| 复制 agents 模块 | 1 天 |
| 创建自定义工具 | 3-5 天 |
| 实现 CLI 界面 | 2-3 天 |
| 编写示例和文档 | 2-3 天 |
| 测试和优化 | 2-3 天 |

---

## 2. 环境准备

### 2.1 系统要求

- Python 3.8+
- Git
- Anthropic API 密钥

### 2.2 创建项目目录

```bash
# 1. 创建项目根目录
mkdir dev-agent
cd dev-agent

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2.4 设置环境变量

**方法一：临时设置（当前终端会话）**

```bash
export ANTHROPIC_API_KEY='your-api-key'
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
# 可选：指定模型名称
export ANTHROPIC_MODEL=glm-5
```

**方法二：创建 .env 文件（推荐）**

创建 `.env` 文件：

```bash
# .env
ANTHROPIC_API_KEY=your-api-key
ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
# 可选：指定模型名称
# ANTHROPIC_MODEL=glm-5
```

**支持的模型**：`glm-5` (默认), `qwen3.5-plus`, `qwen3-max-2026-01-23`, `qwen3-coder-next`, `qwen3-coder-plus`, `glm-4.7`, `kimi-k2.5`, `MiniMax-M2.5`

---

## 3. 项目结构

### 3.1 创建目录结构

```bash
# 创建目录结构
mkdir -p agents/tools agents/utils
mkdir -p custom_tools
mkdir -p examples
mkdir -p storage
```

### 3.2 完整目录结构

```
dev-agent/
├── .env                     # 环境变量（不提交到 git）
├── .env.example             # 环境变量示例
├── .gitignore               # Git 忽略文件
├── README.md                # 项目说明
├── requirements.txt         # Python 依赖
├── config.py                # 配置管理
├── cli.py                   # CLI 入口
│
├── agents/                  # 从 quickstarts 复制
│   ├── __init__.py
│   ├── agent.py             # Agent 核心
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py          # 工具基类
│   │   ├── file_tools.py    # 文件工具
│   │   ├── think.py         # 思考工具
│   │   ├── calculator_mcp.py
│   │   └── code_execution.py
│   └── utils/
│       ├── __init__.py
│       ├── connections.py   # MCP 连接
│       ├── history_util.py  # 消息历史
│       └── tool_util.py     # 工具执行
│
├── custom_tools/            # 自定义工具
│   ├── __init__.py
│   ├── git_tool.py          # Git 工具
│   ├── shell_tool.py        # Shell 工具
│   └── project_tool.py      # 项目生成工具
│
├── examples/                # 示例脚本
│   ├── basic_chat.py        # 基础对话示例
│   └── create_project.py    # 创建项目示例
│
└── storage/                 # 存储目录
    ├── workflows/           # 工作流数据
    └── checkpoints/         # 检查点
```

---

## 4. 安装依赖

### 4.1 创建 requirements.txt

```
# requirements.txt

# Anthropic SDK
anthropic>=0.18.0

# MCP (Model Context Protocol)
mcp>=0.1.0

# 开发工具
rich>=13.0.0              # 终端美化
click>=8.0.0              # CLI 框架
python-dotenv>=1.0.0      # .env 文件支持

# 测试
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

### 4.2 安装依赖

```bash
pip install -r requirements.txt
```

---

## 5. 复制 agents 模块

### 5.1 从 quickstarts 复制

```bash
# 假设 claude-quickstarts 在同一目录下
cp -r ../claude-quickstarts/agents/* ./agents/
```

**或者手动复制以下文件**：

| 源文件 | 目标文件 |
|--------|----------|
| `claude-quickstarts/agents/__init__.py` | `agents/__init__.py` |
| `claude-quickstarts/agents/agent.py` | `agents/agent.py` |
| `claude-quickstarts/agents/tools/*` | `agents/tools/*` |
| `claude-quickstarts/agents/utils/*` | `agents/utils/*` |

### 5.2 验证复制

确保以下文件存在：
- `agents/agent.py`
- `agents/tools/base.py`
- `agents/tools/file_tools.py`
- `agents/tools/think.py`
- `agents/utils/history_util.py`
- `agents/utils/connections.py`
- `agents/utils/tool_util.py`

---

## 6. 创建自定义工具

### 6.1 Git 工具

创建 `custom_tools/git_tool.py`：

```python
"""Git 版本控制工具"""

import subprocess
from agents.tools.base import Tool


class GitTool(Tool):
    """Git 工具 - 执行常见 Git 操作"""

    def __init__(self):
        super().__init__(
            name="git",
            description="""
            执行 Git 版本控制操作。

            支持的命令:
            - init: 初始化仓库
            - add: 添加文件
            - commit: 提交更改
            - status: 查看状态
            - log: 查看历史
            - branch: 分支管理
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Git 命令",
                        "enum": ["init", "add", "commit", "status", "log", "branch"],
                    },
                    "args": {
                        "type": "string",
                        "description": "命令参数",
                    },
                    "message": {
                        "type": "string",
                        "description": "提交消息 (commit 命令需要)",
                    },
                },
                "required": ["command"],
            },
        )

    async def execute(
        self,
        command: str,
        args: str = "",
        message: str = "",
    ) -> str:
        """执行 Git 命令

        参数:
            command: Git 命令
            args: 命令参数
            message: 提交消息

        返回:
            命令输出或错误信息
        """
        try:
            cmd = ["git", command]

            if args:
                cmd.extend(args.split())

            if command == "commit" and message:
                cmd.extend(["-m", message])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
            )

            if result.returncode == 0:
                return result.stdout or "命令执行成功"
            else:
                return f"Git 错误：{result.stderr}"

        except subprocess.TimeoutExpired:
            return "Git 命令超时 (超过 30 秒)"
        except Exception as e:
            return f"执行 Git 命令失败：{str(e)}"
```

### 6.2 Shell 工具

创建 `custom_tools/shell_tool.py`：

```python
"""Shell 命令执行工具"""

import subprocess
from agents.tools.base import Tool


class ShellTool(Tool):
    """Shell 工具 - 执行安全的 Shell 命令"""

    def __init__(self):
        super().__init__(
            name="shell",
            description="""
            执行 Shell 命令。

            安全限制:
            - 仅限开发相关命令 (npm, pip, python, node 等)
            - 禁止危险命令 (rm -rf, sudo 等)
            - 超时限制 60 秒
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 Shell 命令",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "工作目录",
                    },
                },
                "required": ["command"],
            },
        )

        # 禁止的命令列表
        self.blocked_commands = [
            "rm -rf",
            "sudo",
            "dd",
            "mkfs",
        ]

    async def execute(self, command: str, cwd: str = None) -> str:
        """执行 Shell 命令

        参数:
            command: Shell 命令
            cwd: 工作目录

        返回:
            命令输出或错误信息
        """
        # 安全检查
        for blocked in self.blocked_commands:
            if blocked in command:
                return f"安全限制：命令包含被禁止的操作 '{blocked}'"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=cwd,
                encoding="utf-8",
            )

            output = result.stdout
            if result.stderr:
                output += f"\n错误：{result.stderr}"

            return output or "命令执行成功"

        except subprocess.TimeoutExpired:
            return "命令执行超时 (超过 60 秒)"
        except Exception as e:
            return f"执行命令失败：{str(e)}"
```

### 6.3 项目生成工具

创建 `custom_tools/project_tool.py`：

```python
"""项目生成工具"""

import os
from pathlib import Path
from agents.tools.base import Tool


class ProjectTool(Tool):
    """项目生成工具 - 创建项目结构"""

    def __init__(self):
        super().__init__(
            name="project",
            description="""
            创建项目结构和文件。

            操作:
            - create_dir: 创建目录
            - create_file: 创建文件
            - list_template: 列出可用模板
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "操作类型",
                        "enum": ["create_dir", "create_file", "list_template"],
                    },
                    "path": {
                        "type": "string",
                        "description": "路径",
                    },
                    "content": {
                        "type": "string",
                        "description": "文件内容 (create_file 需要)",
                    },
                },
                "required": ["operation", "path"],
            },
        )

    async def execute(
        self,
        operation: str,
        path: str,
        content: str = "",
    ) -> str:
        """执行项目操作

        参数:
            operation: 操作类型
            path: 路径
            content: 文件内容

        返回:
            操作结果
        """
        try:
            if operation == "create_dir":
                return self._create_dir(path)
            elif operation == "create_file":
                return self._create_file(path, content)
            elif operation == "list_template":
                return self._list_template()
            else:
                return f"错误：未知操作 '{operation}'"
        except Exception as e:
            return f"执行失败：{str(e)}"

    def _create_dir(self, path: str) -> str:
        """创建目录"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return f"目录已创建：{path}"
        except Exception as e:
            return f"创建目录失败：{str(e)}"

    def _create_file(self, path: str, content: str) -> str:
        """创建文件"""
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"文件已创建：{path} ({len(content)} 字符)"
        except Exception as e:
            return f"创建文件失败：{str(e)}"

    def _list_template(self) -> str:
        """列出模板"""
        templates = [
            "python_package - Python 包模板",
            "nodejs_app - Node.js 应用模板",
            "react_app - React 应用模板",
        ]
        return "可用模板:\n" + "\n".join(f"  - {t}" for t in templates)
```

### 6.4 自定义工具 __init__.py

创建 `custom_tools/__init__.py`：

```python
"""自定义工具模块"""

from .git_tool import GitTool
from .shell_tool import ShellTool
from .project_tool import ProjectTool

__all__ = ["GitTool", "ShellTool", "ProjectTool"]
```

---

## 7. 创建配置文件

创建 `config.py`：

```python
"""DevAgent 配置管理"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    """模型配置"""

    model: str = "glm-5"  # 默认模型
    max_tokens: int = 4096  # 最大生成 token
    temperature: float = 0.7  # 温度参数


@dataclass
class AgentConfig:
    """Agent 配置"""

    name: str = "DevAgent"
    verbose: bool = True
    system_prompt: Optional[str] = None


@dataclass
class ToolConfig:
    """工具配置"""

    # Git 工具配置
    git_author_name: str = "DevAgent"
    git_author_email: str = "devagent@local"

    # Shell 工具配置
    shell_timeout: int = 60  # 秒

    # 文件工具配置
    max_file_size: int = 1024 * 1024  # 1MB


def load_env():
    """加载环境变量"""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file)


def get_api_key() -> str:
    """获取 API 密钥"""
    load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "请设置 ANTHROPIC_API_KEY 环境变量 "
            "或创建 .env 文件"
        )
    return api_key


# 默认配置实例
DEFAULT_MODEL_CONFIG = ModelConfig()
DEFAULT_AGENT_CONFIG = AgentConfig()
DEFAULT_TOOL_CONFIG = ToolConfig()
```

---

## 8. 创建 CLI 入口

创建 `cli.py`：

```python
"""DevAgent 命令行入口"""

import asyncio
import os
from agents.agent import Agent
from agents.tools.think import ThinkTool
from agents.tools.file_tools import FileReadTool, FileWriteTool
from custom_tools.git_tool import GitTool
from custom_tools.shell_tool import ShellTool
from config import get_api_key, DEFAULT_MODEL_CONFIG


async def main():
    """主函数"""
    # 检查 API 密钥
    try:
        api_key = get_api_key()
        os.environ["ANTHROPIC_API_KEY"] = api_key
    except ValueError as e:
        print(f"错误：{e}")
        print("\n请设置环境变量:")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        print("\n或创建 .env 文件")
        return

    # 创建 Agent
    print("=" * 50)
    print("DevAgent 基础单 Agent 系统")
    print("=" * 50)
    print("\n正在初始化 DevAgent...")

    agent = Agent(
        name="DevAgent",
        system="""你是一个专业的软件开发助手。你可以帮助用户:

1. 创建项目结构和初始化代码
2. 编写和修改代码文件
3. 执行 Git 版本控制操作
4. 运行开发命令和测试

请逐步思考每个任务，使用可用的工具来完成工作。
如果不确定，请先使用 think 工具进行推理。""",
        tools=[
            ThinkTool(),          # 思考工具
            FileReadTool(),       # 读取文件
            FileWriteTool(),      # 写入文件
            GitTool(),            # Git 操作
            ShellTool(),          # Shell 命令
        ],
        verbose=True,
    )

    print("DevAgent 已就绪！")
    print("\n可用命令:")
    print("  - 输入你的需求，例如：'创建一个 Python 计算器项目'")
    print("  - 输入 'quit' 或 'q' 退出")
    print("  - 输入 'help' 查看帮助")
    print("=" * 50)

    # 主循环
    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n再见！")
                break

            if user_input.lower() == "help":
                print_help()
                continue

            # 运行 Agent
            response = await agent.run_async(user_input)

            # 提取并显示最终响应
            for block in response.content:
                if block.type == "text":
                    print(f"\n{block.text}")

        except KeyboardInterrupt:
            print("\n中断，继续输入以继续使用。")
        except Exception as e:
            print(f"\n发生错误：{str(e)}")


def print_help():
    """打印帮助信息"""
    print("""
DevAgent 帮助信息

可用命令:
  <你的需求>     - 描述你要完成的任务
  help          - 显示此帮助信息
  quit/q/exit   - 退出程序

示例:
  > 创建一个 Python 计算器项目
  > 帮我写一个 Hello World 的 Python 脚本
  > 初始化一个 Git 仓库并提交

工具说明:
  - think: 内部推理
  - file_read: 读取文件
  - file_write: 写入/编辑文件
  - git: Git 操作
  - shell: Shell 命令
""")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 9. 创建示例脚本

### 9.1 基础对话示例

创建 `examples/basic_chat.py`：

```python
"""基础对话示例"""

import asyncio
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent import Agent
from agents.tools.think import ThinkTool
from config import get_api_key


async def main():
    """基础对话示例"""
    # 设置 API 密钥
    os.environ["ANTHROPIC_API_KEY"] = get_api_key()

    # 创建简单 Agent
    print("创建 ChatAgent...")
    agent = Agent(
        name="ChatAgent",
        system="你是一个友好的聊天助手。请用简洁的方式回答问题。",
        tools=[ThinkTool()],
        verbose=True,
    )

    # 测试对话
    print("\n测试对话:")
    print("-" * 40)

    questions = [
        "你好，请介绍一下自己",
        "Python 和 JavaScript 有什么区别？",
        "如何学习编程？",
    ]

    for question in questions:
        print(f"\n问：{question}")
        response = await agent.run_async(question)

        for block in response.content:
            if block.type == "text":
                print(f"答：{block.text[:200]}...")

        print("-" * 40)

    print("\n示例完成！")


if __name__ == "__main__":
    asyncio.run(main())
```

### 9.2 创建项目示例

创建 `examples/create_project.py`：

```python
"""创建项目示例"""

import asyncio
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent import Agent
from agents.tools.file_tools import FileReadTool, FileWriteTool
from custom_tools.git_tool import GitTool
from custom_tools.project_tool import ProjectTool
from config import get_api_key


async def main():
    """创建项目示例"""
    # 设置 API 密钥
    os.environ["ANTHROPIC_API_KEY"] = get_api_key()

    # 创建项目目录
    project_dir = "./demo_project"

    print("创建 ProjectAgent...")
    agent = Agent(
        name="ProjectAgent",
        system="你是一个项目初始化助手。帮助用户创建项目结构和文件。",
        tools=[
            FileReadTool(),
            FileWriteTool(),
            GitTool(),
            ProjectTool(),
        ],
        verbose=True,
    )

    # 创建 Python 项目
    print(f"\n创建 Python 项目到 {project_dir}")
    print("-" * 40)

    response = await agent.run_async(
        f"请在 {project_dir} 目录创建一个 Python 项目，包含:"
        "1. main.py - Hello World 程序"
        "2. README.md - 项目说明"
        "3. requirements.txt - 依赖文件"
        "然后初始化 Git 仓库并提交"
    )

    # 显示结果
    print("\n结果:")
    for block in response.content:
        if block.type == "text":
            print(block.text)

    print("\n示例完成！")
    print(f"查看项目：cd {project_dir} && ls -la")


if __name__ == "__main__":
    asyncio.run(main())
```

### 9.3 示例 __init__.py

创建 `examples/__init__.py`：

```python
"""示例脚本模块"""
```

---

## 10. 创建项目文档

### 10.1 README.md

创建 `README.md`：

```markdown
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
```

### 3. 运行 CLI

```bash
python cli.py
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
├── cli.py              # CLI 入口
├── config.py           # 配置管理
├── agents/             # Agent 模块
├── custom_tools/       # 自定义工具
├── examples/           # 示例脚本
└── storage/            # 存储目录
```

## 文档

- [阶段 1 实施指南](./design/PHASE1.md)
- [总体设计](./design/DESIGN.md)

## License

MIT
```

### 10.2 .gitignore

创建 `.gitignore`：

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# 项目输出
demo_project/
*.log

# 存储
storage/workflows/*
storage/checkpoints/*
!storage/.gitkeep
```

---

## 11. 运行和测试

### 11.1 运行 CLI

```bash
# 激活虚拟环境
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 运行 CLI
python cli.py
```

### 11.2 测试对话

```
> 创建一个 Python 计算器项目

[DevAgent] Received: 创建一个 Python 计算器项目
[DevAgent] Tool call: file_write(operation=write, path=calculator.py)
[DevAgent] Tool call: file_write(operation=write, path=README.md)
[DevAgent] Tool call: git(command=init, args=)
[DevAgent] Tool call: git(command=add, args=.)
[DevAgent] Tool call: git(command=commit, args=, message=初始化计算器项目)

输出：项目创建完成！
```

### 11.3 运行示例

```bash
# 基础对话示例
python examples/basic_chat.py

# 创建项目示例
python examples/create_project.py
```

---

## 12. 阶段 1 检查清单

完成以下任务后，阶段 1 即完成：

### 环境准备

- [ ] 创建项目目录
- [ ] 创建虚拟环境
- [ ] 设置 API 密钥

### 项目结构

- [ ] 创建目录结构
- [ ] 创建 requirements.txt
- [ ] 安装依赖

### agents 模块

- [ ] 从 quickstarts 复制 agents 模块
- [ ] 验证所有文件存在

### 自定义工具

- [ ] 创建 GitTool 并测试
- [ ] 创建 ShellTool 并测试
- [ ] 创建 ProjectTool 并测试

### CLI 界面

- [ ] 创建 cli.py
- [ ] 创建 config.py
- [ ] 运行 CLI 并测试

### 示例和文档

- [ ] 创建 basic_chat.py
- [ ] 创建 create_project.py
- [ ] 创建 README.md
- [ ] 创建 .gitignore

### 测试

- [ ] 运行 CLI 并创建项目
- [ ] 运行示例脚本
- [ ] 验证 Git 功能

---

## 下一步

完成阶段 1 后，继续阅读 [PHASE2.md](./PHASE2.md) 开始实现多 Agent 协作系统。
