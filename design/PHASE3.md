# 阶段 3 实施指南：完备生产系统

> **时间**: 8-12 周
>
> **目标**: 功能完备的生产级系统

---

## 1. 阶段 3 概述

### 1.1 目标

完成阶段 3 后，你将拥有：
- 完整的 CLI TUI 界面
- Web 可视化界面
- REST API
- 完善的日志和监控系统
- 完整的文档和测试

### 1.2 交付物

| 交付物 | 说明 |
|--------|------|
| CLI TUI | 丰富的终端界面 |
| Web UI | React 可视化面板 |
| REST API | FastAPI 接口 |
| 日志系统 | 完整日志记录 |
| 监控系统 | 工作流监控 |
| 完整文档 | API 文档 + 用户指南 |
| 测试套件 | 单元 + 集成测试 |

### 1.3 新增组件

```
dev-agent/
├── ... (阶段 1+2 的文件)
│
├── cli/                   # 新增：CLI 界面
│   ├── __init__.py
│   ├── main.py            # CLI 主程序
│   ├── commands/          # 命令模块
│   │   ├── start.py       # 启动命令
│   │   ├── status.py      # 状态命令
│   │   ├── list.py        # 列表命令
│   │   └── resume.py      # 恢复命令
│   └── ui/                # TUI 界面
│       ├── app.py         # TUI 应用
│       └── components.py  # UI 组件
│
├── web/                   # 新增：Web 界面
│   ├── app/               # Next.js 应用
│   │   ├── page.tsx       # 主页
│   │   ├── components/    # React 组件
│   │   └── api/           # API 路由
│   ├── package.json
│   └── next.config.mjs
│
├── api/                   # 新增：REST API
│   ├── __init__.py
│   ├── main.py            # FastAPI 应用
│   └── routes/            # API 路由
│
├── core/                  # 重构：核心引擎
│   ├── engine.py          # 核心引擎
│   ├── agents/            # Agent 模块
│   └── tools/             # 工具模块
│
├── storage/               # 存储
│   ├── workflows/         # 工作流数据
│   ├── checkpoints/       # 检查点
│   └── logs/              # 日志文件
│
└── tests/                 # 测试
    ├── unit/              # 单元测试
    ├── integration/       # 集成测试
    └── e2e/               # 端到端测试
```

---

## 2. CLI TUI 界面

### 2.1 依赖安装

```bash
# 添加 TUI 依赖
pip install rich click prompt-toolkit
```

### 2.2 创建 CLI 主程序

创建 `cli/main.py`：

```python
"""DevAgent CLI 主程序"""

import click
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from orchestrator.workflow_engine import WorkflowEngine
from orchestrator.context_store import ContextStore
from config import get_api_key
import os

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """DevAgent - 多 Agent 软件开发系统"""
    pass


@cli.command()
@click.argument("request")
@click.option(
    "--workflow-id",
    "-w",
    help="恢复指定的工作流",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="启用详细输出",
)
def run(request: str, workflow_id: str, verbose: bool):
    """运行新的工作流或恢复已有工作流"""
    os.environ["ANTHROPIC_API_KEY"] = get_api_key()

    async def execute():
        engine = WorkflowEngine()

        if workflow_id:
            # 恢复已有工作流
            console.print(
                Panel(f"恢复工作流：{workflow_id}", title="Resume")
            )
            result = await engine.resume_from_checkpoint(workflow_id)
        else:
            # 执行新工作流
            console.print(
                Panel(f"用户需求：{request}", title="New Workflow")
            )
            result = await engine.execute(request)

        # 显示结果
        display_result(result)

    asyncio.run(execute())


@cli.command()
@click.option(
    "--limit",
    "-l",
    default=10,
    help="显示最近的工作流数量",
)
def list_workflows(limit: int):
    """列出最近的工作流"""
    store = ContextStore()
    workflows = store.list_workflows()[:limit]

    table = Table(title="最近的工作流")
    table.add_column("Workflow ID", style="cyan")
    table.add_column("用户需求", style="green")
    table.add_column("完成阶段", style="yellow")
    table.add_column("创建时间", style="magenta")

    for wf in workflows:
        table.add_row(
            wf["workflow_id"],
            wf["user_request"][:50] + "..." if len(wf["user_request"]) > 50 else wf["user_request"],
            ", ".join(wf["stages_completed"]),
            wf["created_at"],
        )

    console.print(table)


@cli.command()
@click.argument("workflow_id")
def status(workflow_id: str):
    """显示工作流状态"""
    store = ContextStore()
    context = store.get(workflow_id)

    if not context:
        console.print(f"[red]工作流不存在：{workflow_id}[/red]")
        return

    console.print(Panel(f"工作流：{workflow_id}", title="Status"))
    console.print(f"用户需求：{context.user_request}")
    console.print(f"当前阶段：{context.current_stage}")
    console.print(f"完成阶段：{', '.join(context.stages_completed)}")
    console.print(f"创建时间：{context.created_at}")
    console.print(f"错误：{context.errors if context.errors else '无'}")


@cli.command()
def interactive():
    """进入交互模式"""
    console.print(Panel("DevAgent 交互模式", title="Welcome"))
    console.print("输入你的需求，输入 'quit' 退出\n")

    os.environ["ANTHROPIC_API_KEY"] = get_api_key()
    engine = WorkflowEngine()

    while True:
        request = click.prompt("\n> ", prompt_suffix="")

        if request.lower() in ["quit", "exit", "q"]:
            console.print("再见！")
            break

        if request.lower() == "help":
            print_help()
            continue

        # 执行工作流
        async def execute():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task("执行中...", total=None)
                result = await engine.execute(request)
            display_result(result)

        asyncio.run(execute())


def print_help():
    """打印帮助信息"""
    console.print("""
交互模式帮助:
  - 输入需求描述，例如：'创建一个 Python 计算器项目'
  - 输入 'help' 显示此帮助
  - 输入 'quit' 退出

可用命令 (主 CLI):
  dev-agent run <需求>     - 运行工作流
  dev-agent list           - 列出工作流
  dev-agent status <ID>    - 显示状态
  dev-agent interactive    - 交互模式
  dev-agent --help         - 显示帮助
""")


def display_result(result: dict):
    """显示工作流结果"""
    status = result.get("status", "unknown")
    status_color = "green" if status == "completed" else "red"

    console.print(
        Panel(
            f"[{status_color}]{status}[/{status_color}]",
            title="工作流结果",
        )
    )

    if result.get("errors"):
        console.print("[red]错误:[/red]")
        for error in result["errors"]:
            console.print(f"  - {error}")


if __name__ == "__main__":
    cli()
```

### 2.3 创建 setup.py

创建 `cli/setup.py`（用于安装 CLI）：

```python
"""CLI 安装配置"""

from setuptools import setup

setup(
    name="dev-agent-cli",
    version="1.0.0",
    py_modules=["main"],
    install_requires=[
        "click",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "dev-agent = cli.main:cli",
        ],
    },
)
```

---

## 3. Web 界面

### 3.1 创建 Next.js 项目

```bash
# 创建 Web 目录
mkdir -p web

# 初始化 Next.js 项目
cd web
npx create-next-app@latest . --typescript --tailwind --app
```

### 3.2 主页面

创建 `web/app/page.tsx`：

```tsx
"use client";

import { useState } from "react";

export default function Home() {
  const [request, setRequest] = useState("");
  const [workflowId, setWorkflowId] = useState("");
  const [status, setStatus] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const startWorkflow = async () => {
    setStatus("running");
    setLogs(["工作流启动中..."]);

    try {
      const response = await fetch("/api/workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request }),
      });

      const data = await response.json();
      setWorkflowId(data.workflow_id);
      setStatus(data.status);
      setLogs((prev) => [...prev, `工作流 ID: ${data.workflow_id}`]);
    } catch (error) {
      setStatus("error");
      setLogs((prev) => [...prev, `错误：${error}`]);
    }
  };

  return (
    <main className="min-h-screen p-8 bg-gray-900 text-white">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center text-cyan-400">
          DevAgent Web 界面
        </h1>

        {/* 输入区域 */}
        <div className="mb-8">
          <label className="block text-sm font-medium mb-2">
            输入你的需求
          </label>
          <textarea
            value={request}
            onChange={(e) => setRequest(e.target.value)}
            className="w-full p-4 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-cyan-500"
            rows={4}
            placeholder="例如：创建一个 Python 计算器项目..."
          />
          <button
            onClick={startWorkflow}
            className="mt-4 px-6 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg transition"
          >
            启动工作流
          </button>
        </div>

        {/* 状态显示 */}
        {status && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-2">状态</h2>
            <div
              className={`px-4 py-2 rounded-lg inline-block ${
                status === "completed"
                  ? "bg-green-600"
                  : status === "running"
                  ? "bg-yellow-600"
                  : "bg-red-600"
              }`}
            >
              {status}
            </div>
          </div>
        )}

        {/* 日志区域 */}
        <div>
          <h2 className="text-xl font-semibold mb-2">日志</h2>
          <div className="bg-gray-800 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
            {logs.map((log, i) => (
              <div key={i} className="mb-1">
                {log}
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
```

### 3.3 API 路由

创建 `web/app/api/workflow/route.ts`：

```typescript
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { request: userRequest } = body;

    if (!userRequest) {
      return NextResponse.json(
        { error: "请求参数缺失" },
        { status: 400 }
      );
    }

    // 调用 Python 后端
    // 这里需要实现与 Python 后端的通信
    // 可以使用 HTTP、WebSocket 或消息队列

    return NextResponse.json({
      workflow_id: "wf_" + Date.now(),
      status: "running",
    });
  } catch (error) {
    return NextResponse.json(
      { error: String(error) },
      { status: 500 }
    );
  }
}
```

---

## 4. REST API

### 4.1 依赖安装

```bash
pip install fastapi uvicorn pydantic
```

### 4.2 创建 FastAPI 应用

创建 `api/main.py`：

```python
"""DevAgent REST API"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio

from orchestrator.workflow_engine import WorkflowEngine
from orchestrator.context_store import ContextStore

app = FastAPI(
    title="DevAgent API",
    description="多 Agent 软件开发系统 API",
    version="1.0.0",
)

# 允许 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WorkflowRequest(BaseModel):
    """工作流请求"""
    request: str


class WorkflowResponse(BaseModel):
    """工作流响应"""
    workflow_id: str
    status: str
    message: Optional[str] = None


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "DevAgent API",
        "version": "1.0.0",
        "status": "running",
    }


@app.post("/workflow", response_model=WorkflowResponse)
async def start_workflow(data: WorkflowRequest):
    """启动新工作流"""
    engine = WorkflowEngine()

    # 异步执行
    async def execute():
        return await engine.execute(data.request)

    # 启动后台任务
    asyncio.create_task(execute())

    return WorkflowResponse(
        workflow_id="pending",
        status="running",
        message="工作流已启动",
    )


@app.get("/workflow/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """获取工作流状态"""
    store = ContextStore()
    context = store.get(workflow_id)

    if not context:
        raise HTTPException(status_code=404, detail="工作流不存在")

    return {
        "workflow_id": context.workflow_id,
        "user_request": context.user_request,
        "current_stage": context.current_stage,
        "stages_completed": context.stages_completed,
        "created_at": context.created_at,
        "errors": context.errors,
    }


@app.get("/workflows")
async def list_workflows(limit: int = 10):
    """列出工作流"""
    store = ContextStore()
    workflows = store.list_workflows()[:limit]
    return {"workflows": workflows}


@app.post("/workflow/{workflow_id}/resume")
async def resume_workflow(workflow_id: str):
    """恢复工作流"""
    engine = WorkflowEngine()

    async def execute():
        return await engine.resume_from_checkpoint(workflow_id)

    asyncio.create_task(execute())

    return {"message": "工作流恢复中"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 4.3 运行 API

```bash
python api/main.py
```

访问 `http://localhost:8000/docs` 查看 Swagger UI。

---

## 5. 日志系统

### 5.1 创建日志配置

创建 `core/logging_config.py`：

```python
"""日志配置"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_dir: str = "./storage/logs",
    level: str = "INFO",
) -> logging.Logger:
    """设置日志"""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 创建 logger
    logger = logging.getLogger("devagent")
    logger.setLevel(getattr(logging, level.upper()))

    # 格式化
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（轮转）
    file_handler = RotatingFileHandler(
        log_path / "devagent.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 全局 logger
logger = setup_logging()
```

---

## 6. 测试套件

### 6.1 单元测试

创建 `tests/unit/test_workflow_engine.py`：

```python
"""工作流引擎单元测试"""

import pytest
from orchestrator.workflow_engine import WorkflowEngine
from orchestrator.context_store import ContextStore, WorkflowContext


def test_context_creation():
    """测试上下文创建"""
    context = WorkflowContext(user_request="test")
    assert context.workflow_id.startswith("wf_")
    assert context.user_request == "test"
    assert context.stages_completed == []


def test_context_update():
    """测试上下文更新"""
    context = WorkflowContext()
    context.update(requirements_doc="test doc")
    assert context.requirements_doc == "test doc"


def test_context_serialization():
    """测试上下文序列化"""
    context = WorkflowContext(user_request="test")
    context.requirements_doc = "doc"

    data = context.to_dict()
    restored = WorkflowContext.from_dict(data)

    assert restored.user_request == context.user_request
    assert restored.requirements_doc == context.requirements_doc


@pytest.mark.asyncio
async def test_workflow_engine_init():
    """测试引擎初始化"""
    engine = WorkflowEngine()
    assert engine.context_store is not None
    assert engine.checkpoint_manager is not None
```

### 6.2 集成测试

创建 `tests/integration/test_full_workflow.py`：

```python
"""完整工作流集成测试"""

import pytest
import os
from orchestrator.workflow_engine import WorkflowEngine


@pytest.mark.asyncio
async def test_full_workflow():
    """测试完整工作流"""
    os.environ["ANTHROPIC_API_KEY"] = "test-key"

    engine = WorkflowEngine()
    result = await engine.execute("创建测试项目")

    assert "workflow_id" in result
    assert result["status"] in ["completed", "failed"]
```

### 6.3 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行测试
pytest tests/ -v

# 运行覆盖率
pytest tests/ --cov=. --cov-report=html
```

---

## 7. 文档

### 7.1 API 文档

API 文档通过 Swagger UI 自动提供：
- 访问 `http://localhost:8000/docs`

### 7.2 用户指南

创建 `docs/USER_GUIDE.md`：

```markdown
# DevAgent 用户指南

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### CLI 使用

```bash
# 运行工作流
dev-agent run "创建一个 Python 项目"

# 列出工作流
dev-agent list

# 查看状态
dev-agent status <workflow_id>

# 交互模式
dev-agent interactive
```

### API 使用

```bash
# 启动 API 服务器
python api/main.py

# 调用 API
curl -X POST http://localhost:8000/workflow \
  -H "Content-Type: application/json" \
  -d '{"request": "创建测试项目"}'
```

### Web 界面

访问 `http://localhost:3000`
```

---

## 8. 阶段 3 检查清单

完成以下任务后，阶段 3 即完成：

### CLI TUI

- [ ] 创建 CLI 主程序
- [ ] 实现 run 命令
- [ ] 实现 list 命令
- [ ] 实现 status 命令
- [ ] 实现 interactive 模式
- [ ] 安装测试

### Web UI

- [ ] 创建 Next.js 项目
- [ ] 实现主页面
- [ ] 实现 API 路由
- [ ] 工作流状态显示
- [ ] 日志实时显示

### REST API

- [ ] 创建 FastAPI 应用
- [ ] 实现 /workflow 端点
- [ ] 实现 /workflow/{id} 端点
- [ ] 实现 /workflows 端点
- [ ] Swagger UI 测试

### 日志系统

- [ ] 创建日志配置
- [ ] 实现日志轮转
- [ ] 集成到各组件

### 测试

- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 运行测试套件
- [ ] 覆盖率报告

### 文档

- [ ] API 文档
- [ ] 用户指南
- [ ] 部署文档
- [ ] README 更新

### 发布

- [ ] 版本号设置
- [ ] Changelog
- [ ] v1.0 发布

---

## 完成！

恭喜你完成阶段 3！现在你有一个功能完备的 DevAgent 系统：

- ✅ CLI TUI 界面
- ✅ Web 可视化界面
- ✅ REST API
- ✅ 完整日志系统
- ✅ 测试套件
- ✅ 完整文档

下一步可以考虑：
- 性能优化
- 添加更多工具
- 支持分布式部署
- 集成更多 AI 模型
