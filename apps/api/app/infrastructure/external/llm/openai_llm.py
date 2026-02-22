"""OpenAI LLM 实现模块.

该模块提供了基于 OpenAI SDK 的 LLM 调用实现，支持标准 OpenAI API
以及兼容 OpenAI 格式的第三方服务（如 DeepSeek、Azure 等）。
"""

import logging
from typing import Any

from openai import AsyncOpenAI

from app.application.errors.exceptions import ServerRequestsError
from app.domain.external.llm import LLM
from app.domain.models.app_config import LLMConfig

logger = logging.getLogger(__name__)

# 默认请求超时时间（秒）
DEFAULT_TIMEOUT_SECONDS: float = 3600.0


class OpenAILLM(LLM):
    """基于 OpenAI SDK 的 LLM 调用实现类.

    该类实现了 LLM 协议，提供异步调用 OpenAI 兼容 API 的能力。
    支持工具调用、结构化输出等高级功能。

    Attributes:
        model_name: 当前使用的模型名称.
        temperature: 采样温度参数.
        max_tokens: 最大生成 token 数.
    """

    def __init__(self, llm_config: LLMConfig, **kwargs: Any) -> None:
        """初始化 OpenAI LLM 客户端.

        Args:
            llm_config: LLM 配置对象，包含 API 密钥、基础 URL、模型参数等.
            **kwargs: 额外的客户端配置参数，传递给 AsyncOpenAI.

        Note:
            base_url 会被转换为字符串类型以满足 AsyncOpenAI 的要求.
        """
        self._client = AsyncOpenAI(
            api_key=llm_config.api_key,
            base_url=str(llm_config.base_url),
            **kwargs,
        )
        self._max_tokens = llm_config.max_tokens
        self._temperature = llm_config.temperature
        self._model_name = llm_config.model_name
        self._timeout = DEFAULT_TIMEOUT_SECONDS

    async def invoke(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | None = None,
    ) -> dict[str, Any]:
        """调用 LLM 生成响应.

        Args:
            messages: 消息列表，每条消息包含 role 和 content.
            tools: 可选的工具列表，用于函数调用功能.
            response_format: 可选的响应格式配置，如 JSON Schema.
            tool_choice: 工具选择策略，可选值为:
                - "auto": 自动选择是否调用工具（默认）
                - "required": 强制调用工具
                - "none": 禁止调用工具
                - 特定工具名称: 强制调用指定工具.

        Returns:
            包含生成结果的字典，通常包含 content 和 tool_calls 等字段.

        Raises:
            ServerRequestsError: 当 API 调用失败时抛出.
        """
        try:
            if tools:
                logger.info(
                    "调用 LLM [model=%s, tools=%d]", self._model_name, len(tools)
                )
                response = await self._client.chat.completions.create(  # type: ignore
                    model=self._model_name,
                    temperature=float(self._temperature),
                    max_tokens=int(self._max_tokens),
                    messages=messages,
                    response_format=response_format,
                    tools=tools,
                    tool_choice=tool_choice,
                    parallel_tool_calls=False,
                    timeout=self._timeout,
                )
            else:
                logger.info("调用 LLM [model=%s]", self._model_name)
                response = await self._client.chat.completions.create(  # type: ignore
                    model=self._model_name,
                    temperature=float(self._temperature),
                    max_tokens=int(self._max_tokens),
                    messages=messages,
                    response_format=response_format,
                    timeout=self._timeout,
                )

            result = response.choices[0].message.model_dump()
            logger.debug("LLM 响应: %s", result)
            return result

        except Exception as e:
            logger.exception("LLM 调用失败 [model=%s]: %s", self._model_name, e)
            raise ServerRequestsError(f"调用 {self._model_name} 失败: {str(e)}") from e

    @property
    def model_name(self) -> str:
        """返回当前使用的模型名称."""
        return self._model_name

    @property
    def temperature(self) -> float:
        """返回采样温度参数."""
        return self._temperature

    @property
    def max_tokens(self) -> int:
        """返回最大生成 token 数."""
        return self._max_tokens


if __name__ == "__main__":
    import asyncio

    async def _test_main() -> None:
        """测试函数：演示 OpenAILLM 的基本用法."""
        # pydantic 会自动将字符串转换为 HttpUrl，此处忽略 mypy 类型检查
        config: LLMConfig = LLMConfig(
            base_url="https://api.gpt.ge/v1",  # type: ignore[arg-type]
            api_key="",
            model_name="deepseek-chat",
        )
        llm = OpenAILLM(config)
        response = await llm.invoke([{"role": "user", "content": "Hi"}])
        print(response)

    asyncio.run(_test_main())
