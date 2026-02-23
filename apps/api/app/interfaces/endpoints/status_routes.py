"""系统状态检查路由模块

提供系统健康检查和状态监控相关的API端点。
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.services.status_service import StatusService
from app.domain.models.health_status import HealthStatus
from app.interfaces.schemas import Response
from app.interfaces.service_dependencies import get_health_checker_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/status", tags=["状态模块"])


@router.get(
    "",
    response_model=Response[list[HealthStatus]],
    summary="系统健康检查",
    description="检查系统的postgres、redis、fastapi等组件的状态信息。",
)
async def get_status(
    status_service: Annotated[StatusService, Depends(get_health_checker_service)],
) -> Response:
    """获取系统健康状态

    执行系统健康检查，验证各个组件（数据库、缓存、API服务等）的运行状态。

    Returns:
        Response: 包含系统状态信息的响应对象

    Note:
        当前版本返回简单的成功状态，后续可扩展为返回详细的组件状态信息。
    """
    statues = await status_service.check_all()
    if any(item.status == "error" for item in statues):
        return Response.fail(503, "系统存在服务异常", statues)
    return Response.success(message="系统健康检查成功", data=statues)
