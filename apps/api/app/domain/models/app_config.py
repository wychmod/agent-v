"""应用配置领域模型模块

本模块定义应用程序的配置领域模型，用于管理应用级别的配置信息。

主要模型:
- LLMConfig: 大语言模型配置
- LLMConfigResponse: LLM配置响应模型（脱敏）
- AppConfig: 应用全局配置容器

配置层级:
应用配置采用分层设计，顶层AppConfig聚合各子模块配置，
便于统一管理和扩展。
"""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class LLMConfig(BaseModel):
    """LLM大模型及供应商配置.

    该类用于配置大语言模型(LLM)的连接参数和行为参数，
    包括API地址、认证密钥、模型名称以及生成参数等。

    Attributes:
        base_url: 模型服务的基础URL地址，用于构建API请求.
        api_key: 模型服务的API认证密钥，用于身份验证.
        model_name: 使用的模型名称，默认使用支持推理的deepseek-reasoner模型.
        temperature: 采样温度，控制输出的随机性，范围[0, 2]，值越大越随机.
        max_tokens: 单次请求的最大输出token数，限制响应长度.
    """

    base_url: HttpUrl = HttpUrl("https://api.gpt.ge/v1")
    api_key: str = Field(
        default="",
        description="模型服务的API认证密钥",
    )
    model_name: str = Field(
        default="deepseek-reasoner",
        description="模型名称，默认使用deepseek-reasoner（支持推理），"
        "传递tools参数时会自动切换至deepseek-chat",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="采样温度，控制输出随机性，范围[0, 2]，默认0.7",
    )
    max_tokens: int = Field(
        default=8192,
        ge=1,
        description="单次请求的最大输出token数，默认8192（deepseek-chat模型上限）",
    )

    def to_response(self) -> "LLMConfigResponse":
        """转换为响应模型（排除敏感信息）"""
        return LLMConfigResponse(
            base_url=self.base_url,
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )


class LLMConfigResponse(BaseModel):
    """LLM配置响应模型（不含敏感信息）.

    用于API响应，排除api_key等敏感字段。
    """

    base_url: HttpUrl
    model_name: str
    temperature: float
    max_tokens: int


class AppConfig(BaseModel):
    """应用全局配置信息.

    该类作为应用程序的顶层配置容器，聚合所有子模块配置。
    支持动态扩展字段，便于在不修改模型的情况下添加新配置项。

    Attributes:
        llm_config: LLM大模型配置对象.
    """

    llm_config: LLMConfig = Field(
        description="LLM大模型及供应商配置",
    )

    # Pydantic配置：允许传递额外字段，支持配置的动态扩展
    model_config = ConfigDict(extra="allow")
