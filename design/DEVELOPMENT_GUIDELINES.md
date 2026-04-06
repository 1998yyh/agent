# DevAgent 开发规范

> 版本：1.0
>
> 创建日期：2026-04-05

---

## 1. 代码风格规范

### 1.1 Python 代码规范

| 项目 | 规范 |
|------|------|
| **命名风格** | 变量/函数：`snake_case`，类：`PascalCase`，常量：`UPPER_CASE` |
| **类型注解** | 所有公共 API 必须有类型注解 |
| **文档字符串** | 所有公开函数/类必须有 docstring（中文） |
| **最大行宽** | 100 字符 |
| **格式化** | 使用 `ruff format`（兼容 Black） |
| **Lint** | 使用 `ruff check` |

**示例**：

```python
"""Git 工具模块 - 提供版本控制功能"""

from typing import Optional
from agents.tools.base import Tool


class GitTool(Tool):
    """Git 工具 - 执行常见 Git 操作"""

    def __init__(self):
        super().__init__(
            name="git",
            description="执行 Git 版本控制操作",
        )

    async def execute(
        self,
        command: str,
        args: str = "",
        message: Optional[str] = None,
    ) -> str:
        """执行 Git 命令

        Args:
            command: Git 命令
            args: 命令参数
            message: 提交消息

        Returns:
            命令输出或错误信息
        """
        ...
```

### 1.2 TypeScript 代码规范（Web UI）

| 项目 | 规范 |
|------|------|
| **命名风格** | 变量/函数：`camelCase`，类/组件：`PascalCase` |
| **类型定义** | 优先使用 `interface`，工具类型用 `type` |
| **React 组件** | 必须使用函数组件 + Hooks |
| **格式化** | 使用 Prettier |
| **Lint** | 使用 ESLint |

### 1.3 错误消息规范

| 语言 | 规范 |
|------|------|
| **代码注释** | 中文 |
| **用户可见消息** | 中文 |
| **日志/调试信息** | 英文（便于搜索） |
| **异常类名** | 英文（`WorkflowError`, `ContextNotFoundError`） |

---

## 2. 目录结构规范

```
dev-agent/
├── src/                       # 源代码目录
│   ├── core/                  # 核心引擎
│   │   ├── __init__.py
│   │   ├── engine.py          # 工作流引擎
│   │   ├── context.py         # 上下文管理
│   │   └── checkpoint.py      # 检查点管理
│   │
│   ├── agents/                # Agent 实现
│   │   ├── __init__.py
│   │   ├── base.py            # BaseAgent 基类
│   │   ├── requirements.py    # 需求 Agent
│   │   ├── design.py          # 方案 Agent
│   │   ├── coding.py          # 编码 Agent
│   │   ├── testing.py         # 测试 Agent
│   │   └── delivery.py        # 交付 Agent
│   │
│   ├── tools/                 # 工具实现
│   │   ├── __init__.py
│   │   ├── base.py            # Tool 基类
│   │   ├── file_tools.py      # 文件工具
│   │   ├── git_tool.py        # Git 工具
│   │   ├── shell_tool.py      # Shell 工具
│   │   └── ...
│   │
│   ├── cli/                   # CLI 界面
│   │   ├── __init__.py
│   │   ├── main.py            # CLI 入口
│   │   └── commands/          # 命令模块
│   │
│   ├── api/                   # REST API
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 应用
│   │   └── routes/            # API 路由
│   │
│   └── utils/                 # 工具函数
│       ├── __init__.py
│       ├── logging.py         # 日志配置
│       └── config.py          # 配置管理
│
├── tests/                     # 测试目录（与 src 一对一）
│   ├── __init__.py
│   ├── conftest.py            # Pytest 配置
│   ├── core/                  # 对应 src/core/
│   │   ├── __init__.py
│   │   ├── test_engine.py     # 对应 src/core/engine.py
│   │   ├── test_context.py
│   │   └── test_checkpoint.py
│   ├── agents/                # 对应 src/agents/
│   │   ├── __init__.py
│   │   ├── test_base.py
│   │   ├── test_requirements.py
│   │   └── ...
│   ├── tools/                 # 对应 src/tools/
│   │   ├── __init__.py
│   │   ├── test_base.py
│   │   ├── test_file_tools.py
│   │   └── ...
│   └── integration/           # 集成测试
│       ├── __init__.py
│       └── test_workflow.py
│
├── docs/                      # 文档目录
│   ├── design/                # 设计文档
│   │   ├── DESIGN.md
│   │   ├── PHASE1.md
│   │   ├── PHASE2.md
│   │   ├── PHASE3.md
│   │   └── DEVELOPMENT_GUIDELINES.md
│   │
│   ├── api/                   # API 文档（自动生成 + 手写）
│   │   ├── core.md            # 对应 src/core/
│   │   ├── agents.md          # 对应 src/agents/
│   │   └── tools.md           # 对应 src/tools/
│   │
│   └── user/                  # 用户文档
│       ├── getting-started.md
│       ├── user-guide.md
│       └── faq.md
│
├── examples/                  # 示例脚本
├── scripts/                   # 开发脚本
├── storage/                   # 运行时数据（不提交）
│   ├── workflows/
│   ├── checkpoints/
│   └── logs/
│
├── pyproject.toml             # 项目配置（依赖/脚本）
├── requirements.txt           # 依赖锁定
├── .gitignore
├── .pre-commit-config.yaml    # Git 钩子配置
├── pytest.ini                 # Pytest 配置
├── ruff.toml                  # Ruff 配置
└── README.md
```

### 2.1 关键规范

| 规则 | 说明 |
|------|------|
| **测试文件命名** | `test_<源文件名>.py`，例如 `engine.py` → `test_engine.py` |
| **测试目录结构** | 与 `src/` 目录结构完全平行 |
| **文档组织** | API 文档按模块组织，每个模块一个文档文件 |
| **一对一原则** | 每个公开函数/类 → 必须有测试用例 + 必须有文档字符串 |

---

## 3. 测试规范

### 3.1 测试编写要求

```python
"""测试示例 - test_engine.py"""

import pytest
from src.core.engine import WorkflowEngine


class TestWorkflowEngine:
    """WorkflowEngine 单元测试类"""

    def test_init_creates_engine(self):
        """测试引擎初始化"""
        engine = WorkflowEngine()
        assert engine is not None

    def test_execute_requires_request(self):
        """测试执行需要请求参数"""
        engine = WorkflowEngine()
        with pytest.raises(ValueError):
            await engine.execute("")

    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        """测试执行返回结果"""
        engine = WorkflowEngine()
        result = await engine.execute("测试需求")
        assert "workflow_id" in result
```

### 3.2 测试覆盖率要求

| 模块 | 最低覆盖率 |
|------|-----------|
| **核心引擎** | 90% |
| **Agent 模块** | 85% |
| **工具模块** | 90% |
| **CLI/API** | 70% |
| **整体** | 80% |

### 3.3 测试命名规范

```python
def test_<功能>_<条件>_<预期结果>()
# 例如：
def test_execute_with_empty_request_raises_error()
def test_context_save_persists_to_storage()
```

---

## 4. 文档规范

### 4.1 文档字符串（Docstring）格式

```python
async def execute(
    self,
    command: str,
    args: str = "",
    message: Optional[str] = None,
) -> str:
    """执行 Git 命令

    Args:
        command: Git 命令（init/add/commit/status/log/branch）
        args: 命令参数，空格分隔
        message: 提交消息（commit 命令需要）

    Returns:
        命令输出或错误信息

    Raises:
        GitError: Git 命令执行失败时

    Example:
        >>> tool = GitTool()
        >>> await tool.execute("init")
        '初始化仓库成功'
    """
```

### 4.2 API 文档结构

每个模块的 API 文档（`docs/api/xxx.md`）包含：

```markdown
# 模块名称

## 概述

简要说明模块用途和核心功能。

## 核心类/函数

### ClassName

```python
from src.module import ClassName
```

用途说明。

#### 构造函数

```python
ClassName(param1: str, param2: int = 0)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| param1 | str | 参数说明 |

#### 方法

##### method_name()

```python
result = obj.method_name(arg1, arg2)
```

**返回**: 类型 - 返回值说明

**异常**: 可能抛出的异常

### function_name()

```python
from src.module import function_name
```

函数说明。

## 使用示例

```python
# 示例代码
```
```

---

## 5. Git 提交规范

### 5.1 提交信息格式

```
<类型>(<范围>): <主题>

<正文（可选）>

<页脚（可选）>
```

### 5.2 提交类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(agent): 添加需求分析 Agent` |
| `fix` | Bug 修复 | `fix(tool): 修复 GitTool 超时问题` |
| `docs` | 文档更新 | `docs(readme): 更新安装说明` |
| `style` | 代码格式 | `style(format): Ruff 格式化` |
| `refactor` | 重构 | `refactor(engine): 提取检查点逻辑` |
| `test` | 测试 | `test(engine): 添加单元测试` |
| `chore` | 构建/工具 | `chore(deps): 更新依赖版本` |

### 5.3 提交范围

| 范围 | 说明 |
|------|------|
| `agent` | Agent 相关 |
| `tool` | 工具相关 |
| `engine` | 工作流引擎 |
| `context` | 上下文管理 |
| `cli` | 命令行界面 |
| `api` | REST API |
| `web` | Web 界面 |
| `docs` | 文档 |
| `config` | 配置文件 |

### 5.4 完整示例

```
feat(agent): 添加需求分析 Agent

实现 RequirementsAgent，负责：
- 解析用户需求
- 生成需求文档
- 定义验收标准

Closes #42
```

---

## 6. Code Review 流程

### 6.1 提交审查清单

在提交 PR 前，开发者需确认：

- [ ] 代码通过 `ruff check` 和 `ruff format`
- [ ] 所有测试通过 (`pytest tests/`)
- [ ] 测试覆盖率不低于要求
- [ ] 新增功能有对应测试
- [ ] 公开 API 有 docstring
- [ ] 提交信息符合规范
- [ ] 无调试代码（print 等）

### 6.2 审查要点

| 审查项 | 检查内容 |
|--------|----------|
| **功能正确性** | 代码是否按预期工作 |
| **代码风格** | 是否符合规范 |
| **测试覆盖** | 测试是否充分 |
| **文档完整** | 注释和文档是否齐全 |
| **安全性** | 是否有安全漏洞 |
| **性能** | 是否有性能问题 |

---

## 7. 开发环境设置

### 7.1 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 7.2 配置预提交钩子

```bash
# 安装 pre-commit
pip install pre-commit
pre-commit install
```

### 7.3 运行命令

```bash
# 运行测试
pytest tests/

# 运行覆盖率
pytest tests/ --cov=src --cov-report=html

# 格式化代码
ruff format src/ tests/

# 检查代码
ruff check src/ tests/

# 运行 API 服务器
python -m uvicorn src.api.main:app --reload

# 运行 CLI
python -m src.cli.main
```

---

## 文档历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-04-05 | 初始版本 |

---

*下一步：开始阶段 1 实施，阅读 [PHASE1.md](./PHASE1.md)*
