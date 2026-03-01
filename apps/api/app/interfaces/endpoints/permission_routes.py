"""权限管理 API 路由

本模块提供权限 CRUD 的 API 端点。
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.application.services.role_service import RoleService
from app.domain.models.user import User
from app.interfaces.dependencies.auth_dependencies import (
    get_client_ip,
    get_current_active_user,
    get_role_service,
    get_user_agent,
    require_roles,
)
from app.interfaces.schemas.base import Response
from app.interfaces.schemas.role_schemas import (
    CreatePermissionSchema,
    UpdatePermissionSchema,
)
from app.interfaces.schemas.user_schemas import PermissionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/permissions", tags=["权限管理"])


@router.get(
    "",
    response_model=Response[list[PermissionResponse]],
    summary="获取所有权限",
    description="获取系统中所有权限列表",
)
async def list_permissions(
    _: Annotated[User, Depends(get_current_active_user)],
    role_service: Annotated[RoleService, Depends(get_role_service)],
) -> Response[list[PermissionResponse]]:
    """获取所有权限列表"""
    permissions = await role_service.list_all_permissions()
    return Response.success(
        data=[
            PermissionResponse(
                id=p.id,
                resource=p.resource,
                action=p.action,
                display_name=p.display_name,
                created_at=p.created_at,
            )
            for p in permissions
        ]
    )


@router.post(
    "",
    response_model=Response[PermissionResponse],
    summary="创建权限",
    description="创建新权限（管理员）",
)
async def create_permission(
    data: CreatePermissionSchema,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    role_service: Annotated[RoleService, Depends(get_role_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response[PermissionResponse]:
    """创建新权限"""
    ip_address = get_client_ip(request)
    permission = await role_service.create_permission(
        resource=data.resource,
        action=data.action,
        display_name=data.display_name,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(
        message="权限创建成功",
        data=PermissionResponse(
            id=permission.id,
            resource=permission.resource,
            action=permission.action,
            display_name=permission.display_name,
            created_at=permission.created_at,
        ),
    )


@router.put(
    "/{permission_id}",
    response_model=Response[PermissionResponse],
    summary="更新权限",
    description="更新权限显示名称（管理员）",
)
async def update_permission(
    permission_id: int,
    data: UpdatePermissionSchema,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    role_service: Annotated[RoleService, Depends(get_role_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response[PermissionResponse]:
    """更新权限信息"""
    ip_address = get_client_ip(request)
    permission = await role_service.update_permission(
        permission_id=permission_id,
        display_name=data.display_name,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(
        message="权限更新成功",
        data=PermissionResponse(
            id=permission.id,
            resource=permission.resource,
            action=permission.action,
            display_name=permission.display_name,
            created_at=permission.created_at,
        ),
    )


@router.delete(
    "/{permission_id}",
    response_model=Response,
    summary="删除权限",
    description="删除权限（管理员，会自动从所有角色中移除该权限）",
)
async def delete_permission(
    permission_id: int,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    role_service: Annotated[RoleService, Depends(get_role_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response:
    """删除权限"""
    ip_address = get_client_ip(request)
    await role_service.delete_permission(
        permission_id=permission_id,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(message="权限删除成功")
