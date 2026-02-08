import logging

from fastapi import APIRouter

from app.interfaces.schemas import Response

logging.getLogger(__name__)
router = APIRouter(prefix="/status", tags=["状态模块"])


@router.get(
    "",
    response_model=Response,
    summary="系统健康检查",
    description="检查系统的postgres、redis、fastapi等组件的状态信息。",
)
async def get_status() -> Response:
    return Response.success()
