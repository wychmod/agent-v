"""用户管理 API 路由模块

本模块提供用户管理相关的 API 端点，支持用户自助操作和管理员管理功能。

主要功能:
- 当前用户信息获取和资料更新
- 密码修改
- 用户 CRUD 操作（管理员）
- 用户角色分配和移除（管理员）
- 角色列表和权限查询

API 端点分组:
1. 用户自助操作 (/users/me):
   - GET /users/me: 获取当前用户信息
   - PUT /users/me: 更新个人资料
   - PUT /users/me/password: 修改密码

2. 用户管理（管理员）:
   - POST /users: 创建用户
   - GET /users: 用户列表
   - GET /users/{user_id}: 用户详情
   - PUT /users/{user_id}: 更新用户
   - DELETE /users/{user_id}: 删除用户
   - PUT /users/{user_id}/roles: 分配角色
   - DELETE /users/{user_id}/roles/{role_name}: 移除角色

3. 角色权限查询 (/roles):
   - GET /roles: 角色列表
   - GET /roles/{role_id}/permissions: 角色权限
   - POST /roles/{role_id}/permissions: 分配权限（管理员）
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.application.services.user_service import UserService
from app.domain.models.user import User
from app.interfaces.dependencies.auth_dependencies import (
    get_client_ip,
    get_current_active_user,
    get_user_agent,
    get_user_service,
    require_roles,
)
from app.interfaces.schemas.auth_schemas import ChangePasswordSchema
from app.interfaces.schemas.base import Response
from app.interfaces.schemas.role_schemas import (
    AdminCreateUserSchema,
    AdminUpdateUserSchema,
)
from app.interfaces.schemas.user_schemas import (
    AssignPermissionSchema,
    AssignRoleSchema,
    PermissionResponse,
    RoleResponse,
    UpdateProfileSchema,
    UserDetailResponse,
    UserListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get(
    "/me",
    response_model=Response[UserDetailResponse],
    summary="获取当前用户",
    description="获取当前登录用户的详细信息",
)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Response[UserDetailResponse]:
    return Response.success(data=UserDetailResponse.from_user(current_user))


@router.put(
    "/me",
    response_model=Response[UserDetailResponse],
    summary="更新个人资料",
    description="更新当前用户的个人资料",
)
async def update_profile(
    data: UpdateProfileSchema,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response[UserDetailResponse]:
    ip_address = get_client_ip(request)
    updated_user = await user_service.update_profile(
        user_id=current_user.id,
        username=data.username,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(
        message="资料更新成功", data=UserDetailResponse.from_user(updated_user)
    )


@router.put(
    "/me/password",
    response_model=Response,
    summary="修改密码",
    description="修改当前用户的密码",
)
async def change_password(
    data: ChangePasswordSchema,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response:
    ip_address = get_client_ip(request)
    await user_service.change_password(
        user_id=current_user.id,
        old_password=data.old_password,
        new_password=data.new_password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(message="密码修改成功")


@router.post(
    "",
    response_model=Response[UserDetailResponse],
    summary="创建用户",
    description="管理员创建新用户",
)
async def create_user(
    data: AdminCreateUserSchema,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response[UserDetailResponse]:
    """管理员创建用户"""
    ip_address = get_client_ip(request)
    user = await user_service.create_user_by_admin(
        email=data.email,
        username=data.username,
        password=data.password,
        is_active=data.is_active,
        must_change_password=data.must_change_password,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(
        message="用户创建成功",
        data=UserDetailResponse.from_user(user),
    )


@router.get(
    "",
    response_model=Response[UserListResponse],
    summary="用户列表",
    description="获取用户列表（管理员）",
)
async def list_users(
    _: Annotated[User, Depends(require_roles("admin"))],
    user_service: Annotated[UserService, Depends(get_user_service)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    is_active: Annotated[bool | None, Query()] = None,
) -> Response[UserListResponse]:
    users, total = await user_service.list_users(skip, limit, is_active)
    return Response.success(
        data=UserListResponse(
            items=[UserDetailResponse.from_user(u) for u in users],
            total=total,
            skip=skip,
            limit=limit,
        )
    )


@router.get(
    "/{user_id}",
    response_model=Response[UserDetailResponse],
    summary="获取用户详情",
    description="获取指定用户的详细信息",
)
async def get_user(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Response[UserDetailResponse]:
    if current_user.id != user_id and not current_user.has_role("admin"):
        from app.application.errors.exceptions import ForbiddenError

        raise ForbiddenError(resource="用户", action="查看")

    user = await user_service.get_user(user_id)
    return Response.success(data=UserDetailResponse.from_user(user))


@router.put(
    "/{user_id}",
    response_model=Response[UserDetailResponse],
    summary="更新用户",
    description="管理员更新用户信息",
)
async def update_user(
    user_id: str,
    data: AdminUpdateUserSchema,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response[UserDetailResponse]:
    """管理员更新用户信息"""
    ip_address = get_client_ip(request)
    user = await user_service.update_user_by_admin(
        user_id=user_id,
        username=data.username,
        email=data.email,
        is_active=data.is_active,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(
        message="用户更新成功",
        data=UserDetailResponse.from_user(user),
    )


@router.delete(
    "/{user_id}",
    response_model=Response,
    summary="删除用户",
    description="删除指定用户（管理员）",
)
async def delete_user(
    user_id: str,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response:
    ip_address = get_client_ip(request)
    await user_service.delete_user(
        user_id=user_id,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(message="用户删除成功")


@router.put(
    "/{user_id}/roles",
    response_model=Response,
    summary="分配角色",
    description="为用户分配角色（管理员）",
)
async def assign_role(
    user_id: str,
    data: AssignRoleSchema,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response:
    ip_address = get_client_ip(request)
    await user_service.assign_role(
        user_id=user_id,
        role_name=data.role_name,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(message="角色分配成功")


@router.delete(
    "/{user_id}/roles/{role_name}",
    response_model=Response,
    summary="移除角色",
    description="移除用户的角色（管理员）",
)
async def remove_role(
    user_id: str,
    role_name: str,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response:
    ip_address = get_client_ip(request)
    await user_service.remove_role(
        user_id=user_id,
        role_name=role_name,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(message="角色移除成功")


roles_router = APIRouter(prefix="/roles", tags=["角色权限"])


@roles_router.get(
    "",
    response_model=Response[list[RoleResponse]],
    summary="角色列表",
    description="获取所有角色",
)
async def list_roles(
    _: Annotated[User, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Response[list[RoleResponse]]:
    roles = await user_service.list_all_roles()
    return Response.success(
        data=[
            RoleResponse(
                id=r.id,
                name=r.name,
                display_name=r.display_name,
                description=r.description,
                created_at=r.created_at,
            )
            for r in roles
        ]
    )


@roles_router.get(
    "/{role_id}/permissions",
    response_model=Response[list[PermissionResponse]],
    summary="角色权限",
    description="获取角色的所有权限",
)
async def get_role_permissions(
    role_id: int,
    _: Annotated[User, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Response[list[PermissionResponse]]:
    permissions = await user_service.get_role_permissions(role_id)
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


@roles_router.post(
    "/{role_id}/permissions",
    response_model=Response,
    summary="分配权限",
    description="为角色分配权限（管理员）",
)
async def assign_permission(
    role_id: int,
    data: AssignPermissionSchema,
    request: Request,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response:
    ip_address = get_client_ip(request)
    await user_service.assign_permission_to_role(
        role_id=role_id,
        permission_id=data.permission_id,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(message="权限分配成功")
