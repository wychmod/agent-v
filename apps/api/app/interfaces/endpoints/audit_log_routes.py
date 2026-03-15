"""审计日志 API 路由

本模块提供审计日志查询的 API 端点。
"""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.domain.models.user import User
from app.infrastructure.repositories.mysql_audit_log_repository import (
    MySQLAuditLogRepository,
)
from app.infrastructure.storage.mysql import get_db_session
from app.interfaces.dependencies.auth_dependencies import require_roles
from app.interfaces.schemas.base import Response
from app.interfaces.schemas.user_schemas import AuditLogListResponse, AuditLogResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-logs", tags=["审计日志"])


async def get_audit_log_repository(
    session=Depends(get_db_session),
) -> MySQLAuditLogRepository:
    """获取审计日志仓储"""
    return MySQLAuditLogRepository(session)


@router.get(
    "",
    response_model=Response[AuditLogListResponse],
    summary="查询审计日志",
    description="分页查询系统审计日志，支持多种过滤条件（管理员权限）",
)
async def list_audit_logs(
    _: Annotated[User, Depends(require_roles("admin"))],
    audit_repo: Annotated[MySQLAuditLogRepository, Depends(get_audit_log_repository)],
    skip: Annotated[int, Query(ge=0, description="跳过的记录数")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="每页返回的记录数")] = 20,
    action: Annotated[str | None, Query(description="按操作类型过滤")] = None,
    resource: Annotated[str | None, Query(description="按资源类型过滤")] = None,
    user_id: Annotated[str | None, Query(description="按用户ID过滤")] = None,
    status: Annotated[str | None, Query(description="按操作状态过滤")] = None,
    start_date: Annotated[datetime | None, Query(description="按开始日期过滤")] = None,
    end_date: Annotated[datetime | None, Query(description="按结束日期过滤")] = None,
) -> Response[AuditLogListResponse]:
    """查询审计日志列表

    Args:
        audit_repo: 审计日志仓储
        skip: 跳过的记录数，默认0
        limit: 每页记录数，默认20，最小1，最大100
        action: 操作类型过滤（可选）
        resource: 资源类型过滤（可选）
        user_id: 用户ID过滤（可选）
        status: 操作状态过滤（可选）
        start_date: 开始日期过滤（可选）
        end_date: 结束日期过滤（可选）

    Returns:
        Response[AuditLogListResponse]: 审计日志列表及总数
    """
    # 查询日志列表
    logs = await audit_repo.get_system_logs(
        skip=skip,
        limit=limit,
        user_id=user_id,
        action=action,
        resource=resource,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )

    # 查询总数
    total = await audit_repo.count_system_logs(
        user_id=user_id,
        action=action,
        resource=resource,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )

    # 转换为响应模型
    log_responses = [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            resource=log.resource,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            status=log.status,
            details=log.details,
            created_at=log.created_at,
        )
        for log in logs
    ]

    return Response.success(
        data=AuditLogListResponse(
            items=log_responses,
            total=total,
            skip=skip,
            limit=limit,
        )
    )
