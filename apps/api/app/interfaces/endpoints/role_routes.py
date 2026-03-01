"""角色管理 API 路由

本模块提供角色 CRUD 和角色权限管理的 API 端点。
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.application.services.role_service import RoleService
from app.domain.models.user import User
from app.interfaces.dependencies.auth_dependencies import (
    get_client_ip,
    get_role_service,
    get_user_agent,
    require_roles,
)
from app.interfaces.schemas.base import Response
from app.interfaces.schemas.role_schemas import (
    CreateRoleSchema,
    RoleDetailResponse,
    UpdateRoleSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roles", tags=["角色管理"])


@router.post(
    "",
    response_model=Response[RoleDetailResponse],
    summary="创建角色",
    description="创建新角色（管理员）",
)
async def create_role(
    data: CreateRoleSchema,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    role_service: Annotated[RoleService, Depends(get_role_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response[RoleDetailResponse]:
    """创建新角色"""
    ip_address = get_client_ip(request)
    role = await role_service.create_role(
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(
        message="角色创建成功",
        data=RoleDetailResponse(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            created_at=role.created_at,
            permission_count=len(role.permissions),
            user_count=0,
        ),
    )


@router.put(
    "/{role_id}",
    response_model=Response[RoleDetailResponse],
    summary="更新角色",
    description="更新角色信息（管理员）",
)
async def update_role(
    role_id: int,
    data: UpdateRoleSchema,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    role_service: Annotated[RoleService, Depends(get_role_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response[RoleDetailResponse]:
    """更新角色信息"""
    ip_address = get_client_ip(request)
    role = await role_service.update_role(
        role_id=role_id,
        display_name=data.display_name,
        description=data.description,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(
        message="角色更新成功",
        data=RoleDetailResponse(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            created_at=role.created_at,
            permission_count=len(role.permissions),
            user_count=0,
        ),
    )


@router.delete(
    "/{role_id}",
    response_model=Response,
    summary="删除角色",
    description="删除角色（管理员，不能删除系统保留角色）",
)
async def delete_role(
    role_id: int,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    role_service: Annotated[RoleService, Depends(get_role_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response:
    """删除角色"""
    ip_address = get_client_ip(request)
    await role_service.delete_role(
        role_id=role_id,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(message="角色删除成功")


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    response_model=Response,
    summary="移除角色权限",
    description="从角色中移除指定权限（管理员）",
)
async def remove_role_permission(
    role_id: int,
    permission_id: int,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    role_service: Annotated[RoleService, Depends(get_role_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response:
    """移除角色的权限"""
    ip_address = get_client_ip(request)
    await role_service.remove_permission_from_role(
        role_id=role_id,
        permission_id=permission_id,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(message="权限移除成功")
