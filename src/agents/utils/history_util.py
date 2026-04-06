"""消息历史管理 - 包含 token 跟踪和提示词缓存"""

from typing import Any


class MessageHistory:
    """管理聊天历史，包含 token 跟踪和上下文管理"""

    def __init__(
        self,
        model: str,
        system: str,
        context_window_tokens: int,
        client: Any,
        enable_caching: bool = True,
    ):
        """初始化消息历史

        参数:
            model: 模型名称
            system: 系统提示词
            context_window_tokens: 上下文窗口 token 限制
            client: Anthropic 客户端
            enable_caching: 是否启用缓存（默认 True）
        """
        self.model = model
        self.system = system
        self.context_window_tokens = context_window_tokens
        self.messages: list[dict[str, Any]] = []  # 消息列表
        self.total_tokens = 0  # 总 token 数
        self.enable_caching = enable_caching  # 是否启用缓存
        self.message_tokens: list[tuple[int, int]] = (
            []
        )  # (输入 token, 输出 token) 元组列表
        self.client = client

        # 计算系统提示词的 token 数
        try:
            system_token = (
                self.client.messages.count_tokens(
                    model=self.model,
                    system=self.system,
                    messages=[{"role": "user", "content": "test"}],
                ).input_tokens
                - 1
            )

        except Exception:
            # 如果 API 调用失败，使用估算值（约每 4 个字符 1 个 token）
            system_token = len(self.system) / 4

        self.total_tokens = system_token

    async def add_message(
        self,
        role: str,
        content: str | list[dict[str, Any]],
        usage: Any | None = None,
    ):
        """添加消息到历史记录并跟踪 token 使用

        参数:
            role: 消息角色（user 或 assistant）
            content: 消息内容（字符串或内容块列表）
            usage: token 使用信息
        """
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]

        message = {"role": role, "content": content}
        self.messages.append(message)

        if role == "assistant" and usage:
            # 计算总输入 token（包含缓存 token）
            total_input = (
                usage.input_tokens
                + getattr(usage, "cache_read_input_tokens", 0)
                + getattr(usage, "cache_creation_input_tokens", 0)
            )
            output_tokens = usage.output_tokens

            # 计算当前轮次的输入 token
            current_turn_input = total_input - self.total_tokens
            self.message_tokens.append((current_turn_input, output_tokens))
            self.total_tokens += current_turn_input + output_tokens

    def truncate(self) -> None:
        """当超出上下文窗口限制时，移除最早的消息"""
        if self.total_tokens <= self.context_window_tokens:
            return

        TRUNCATION_NOTICE_TOKENS = 25  # 截断通知的 token 数
        TRUNCATION_MESSAGE = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "[早期历史记录已被截断。]",
                }
            ],
        }

        def remove_message_pair():
            """移除一对消息（用户 + 助手）"""
            self.messages.pop(0)
            self.messages.pop(0)

            if self.message_tokens:
                input_tokens, output_tokens = self.message_tokens.pop(0)
                self.total_tokens -= input_tokens + output_tokens

        # 移除消息直到低于限制
        while (
            self.message_tokens
            and len(self.messages) >= 2
            and self.total_tokens > self.context_window_tokens
        ):
            remove_message_pair()

            # 添加截断通知
            if self.messages and self.message_tokens:
                original_input_tokens, original_output_tokens = (
                    self.message_tokens[0]
                )
                self.messages[0] = TRUNCATION_MESSAGE
                self.message_tokens[0] = (
                    TRUNCATION_NOTICE_TOKENS,
                    original_output_tokens,
                )
                self.total_tokens += (
                    TRUNCATION_NOTICE_TOKENS - original_input_tokens
                )

    def format_for_api(self) -> list[dict[str, Any]]:
        """为 Claude API 格式化消息，支持可选缓存"""
        result = [
            {"role": m["role"], "content": m["content"]} for m in self.messages
        ]

        if self.enable_caching and self.messages:
            # 为最后一条消息添加缓存控制标记
            result[-1]["content"] = [
                {**block, "cache_control": {"type": "ephemeral"}}
                for block in self.messages[-1]["content"]
            ]
        return result
