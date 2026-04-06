"""MCP 服务器连接处理"""

from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import Any, TYPE_CHECKING

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

if TYPE_CHECKING:
    from ..tools.mcp_tool import MCPTool


class MCPConnection(ABC):
    """MCP 服务器连接的基类"""

    def __init__(self):
        self.session = None  # MCP 会话
        self._rw_ctx = None  # 读写上下文
        self._session_ctx = None  # 会话上下文

    @abstractmethod
    async def _create_rw_context(self):
        """根据连接类型创建读写上下文"""

    async def __aenter__(self):
        """初始化 MCP 服务器连接"""
        self._rw_ctx = await self._create_rw_context()
        read_write = await self._rw_ctx.__aenter__()
        read, write = read_write
        self._session_ctx = ClientSession(read, write)
        self.session = await self._session_ctx.__aenter__()
        await self.session.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """清理 MCP 服务器连接资源"""
        try:
            if self._session_ctx:
                await self._session_ctx.__aexit__(exc_type, exc_val, exc_tb)
            if self._rw_ctx:
                await self._rw_ctx.__aexit__(exc_type, exc_val, exc_tb)
        except Exception as e:
            print(f"清理期间出错：{e}")
        finally:
            self.session = None
            self._session_ctx = None
            self._rw_ctx = None

    async def list_tools(self) -> Any:
        """获取 MCP 服务器上可用的工具"""
        response = await self.session.list_tools()
        return response.tools

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """使用提供的参数调用 MCP 服务器上的工具"""
        return await self.session.call_tool(tool_name, arguments=arguments)


class MCPConnectionStdio(MCPConnection):
    """使用标准输入/输出的 MCP 连接"""

    def __init__(
        self, command: str, args: list[str] = [], env: dict[str, str] = None
    ):
        super().__init__()
        self.command = command  # 命令
        self.args = args  # 参数列表
        self.env = env  # 环境变量

    async def _create_rw_context(self):
        return stdio_client(
            StdioServerParameters(
                command=self.command, args=self.args, env=self.env
            )
        )


class MCPConnectionSSE(MCPConnection):
    """使用服务器发送事件 (SSE) 的 MCP 连接"""

    def __init__(self, url: str, headers: dict[str, str] = None):
        super().__init__()
        self.url = url  # SSE 端点 URL
        self.headers = headers or {}  # 请求头

    async def _create_rw_context(self):
        return sse_client(url=self.url, headers=self.headers)


def create_mcp_connection(config: dict[str, Any]) -> MCPConnection:
    """创建 MCP 连接的工厂函数

    参数:
        config: 连接配置字典

    返回:
        适当的 MCP 连接对象
    """
    conn_type = config.get("type", "stdio").lower()

    if conn_type == "stdio":
        if not config.get("command"):
            raise ValueError("STDIO 连接需要提供 command")
        return MCPConnectionStdio(
            command=config["command"],
            args=config.get("args"),
            env=config.get("env"),
        )

    elif conn_type == "sse":
        if not config.get("url"):
            raise ValueError("SSE 连接需要提供 url")
        return MCPConnectionSSE(
            url=config["url"], headers=config.get("headers")
        )

    else:
        raise ValueError(f"不支持的连接类型：{conn_type}")


async def setup_mcp_connections(
    mcp_servers: list[dict[str, Any]] | None,
    stack: AsyncExitStack,
) -> list["MCPTool"]:
    """设置 MCP 服务器连接并创建工具接口

    参数:
        mcp_servers: MCP 服务器配置列表
        stack: 异步退出栈

    返回:
        MCP 工具列表
    """
    # 延迟导入以避免循环导入
    from ..tools.mcp_tool import MCPTool

    if not mcp_servers:
        return []

    mcp_tools = []

    for config in mcp_servers:
        try:
            connection = create_mcp_connection(config)
            await stack.enter_async_context(connection)  # 进入上下文
            tool_definitions = await connection.list_tools()

            for tool_info in tool_definitions:
                mcp_tools.append(
                    MCPTool(
                        name=tool_info.name,
                        description=tool_info.description
                        or f"MCP 工具：{tool_info.name}",
                        input_schema=tool_info.inputSchema,
                        connection=connection,
                    )
                )

        except Exception as e:
            print(f"设置 MCP 服务器 {config} 时出错：{e}")

    print(
        f"已从 {len(mcp_servers)} 个服务器加载 {len(mcp_tools)} 个 MCP 工具。"
    )
    return mcp_tools
