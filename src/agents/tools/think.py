"""思考工具 - 用于内部推理"""

from .base import Tool


class ThinkTool(Tool):
    """用于内部推理的工具，不执行外部操作"""

    def __init__(self):
        super().__init__(
            name="think",  # 工具名称：思考
            description=(
                "使用此工具进行思考。它不会获取新信息或更改数据库，"
                "只是将思考追加到日志中。当需要复杂推理或缓存记忆时使用它。"
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "要记录的思考内容",
                    }
                },
                "required": ["thought"],  # thought 是必需参数
            },
        )

    async def execute(self, thought: str) -> str:
        """简单地将思考内容返回给模型"""
        return "思考完成！"
