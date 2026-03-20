"""应用配置管理 API 路由模块

本模块提供应用配置相关的 API 端点，用于管理系统运行时配置。

主要功能:
- LLM（大语言模型）配置的获取和更新

API 端点:
- GET /app-config/llm: 获取 LLM 配置信息
- POST /app-config/llm: 更新 LLM 配置信息

Note:
    配置的修改会立即生效，无需重启服务
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.services.app_config_service import AppConfigService
from app.domain.models.app_config import LLMConfig, LLMConfigResponse
from app.interfaces.schemas import Response
from app.interfaces.service_dependencies import get_app_config_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/app-config", tags=["设置模块"])


@router.get(
    path="/llm",
    response_model=Response[LLMConfigResponse],
    summary="获取LLM配置信息",
    description="包含LLM提供商的base_url、temperature、model_name、max_tokens",
)
async def get_llm_config(
    app_config_service: Annotated[AppConfigService, Depends(get_app_config_service)],
) -> Response[LLMConfigResponse]:
    """获取 LLM 配置信息

    返回当前 LLM 服务的配置参数，不包含敏感的 API 密钥信息。

    Returns:
        Response[LLMConfigResponse]: 包含 LLM 配置的响应对象
    """
    llm_config = await app_config_service.get_llm_config()
    return Response.success(data=llm_config.to_response())


@router.post(
    path="/llm",
    response_model=Response[LLMConfigResponse],
    summary="更新LLM配置信息",
    description="更新LLM配置信息，当api_key为空的时候表示不更新该字段",
)
async def update_llm_config(
    new_llm_config: LLMConfig,
    app_config_service: Annotated[AppConfigService, Depends(get_app_config_service)],
) -> Response[LLMConfigResponse]:
    """更新 LLM 配置信息

    更新 LLM 服务配置，支持部分字段更新。
    当 api_key 为空时，保留原有的 API 密钥不变。

    Args:
        new_llm_config: 新的 LLM 配置对象

    Returns:
        Response[LLMConfigResponse]: 包含更新后 LLM 配置的响应对象
    """
    updated_llm_config = await app_config_service.update_llm_config(new_llm_config)
    return Response.success(
        message="更新LLM信息配置成功",
        data=updated_llm_config.to_response(),
    )
