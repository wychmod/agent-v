"""大语言模型协议模块

本模块定义与大语言模型（LLM）交互的接口协议。

支持特性:
- 消息列表对话
- 工具调用（Function Calling）
- 响应格式控制
- 模型参数配置
"""

from typing import Any, Protocol


class LLM(Protocol):
    """大语言模型协议

    定义与LLM交互的接口契约。
    支持对话、工具调用等AI应用场景。
    """

    async def invoke(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | None = None,
    ) -> dict[str, Any]:
        """调用LLM生成响应

        Args:
            messages: 消息列表，每个消息包含role和content
            tools: 可用工具列表（Function定义）
            response_format: 响应格式约束
            tool_choice: 工具选择策略（auto、none、required等）

        Returns:
            LLM响应数据，包含生成内容和工具调用等信息
        """
        ...

    @property
    def model_name(self) -> str:
        """获取模型名称"""
        ...

    @property
    def temperature(self) -> float:
        """获取采样温度"""
        ...

    @property
    def max_tokens(self) -> int:
        """获取最大生成token数"""
        ...
