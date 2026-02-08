"""系统状态检查路由模块

提供系统健康检查和状态监控相关的API端点。
"""

import logging

from fastapi import APIRouter

from app.interfaces.schemas import Response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/status", tags=["状态模块"])


@router.get(
    "",
    response_model=Response,
    summary="系统健康检查",
    description="检查系统的postgres、redis、fastapi等组件的状态信息。",
)
async def get_status() -> Response:
    """获取系统健康状态

    执行系统健康检查，验证各个组件（数据库、缓存、API服务等）的运行状态。

    Returns:
        Response: 包含系统状态信息的响应对象

    Note:
        当前版本返回简单的成功状态，后续可扩展为返回详细的组件状态信息。
    """
    return Response.success()
