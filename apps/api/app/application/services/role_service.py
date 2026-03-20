"""角色和权限管理服务模块

本模块提供角色（Role）和权限（Permission）的完整管理功能。

主要功能:
- 角色的创建、更新、删除和查询
- 权限的创建、更新、删除和查询
- 角色权限的分配和移除
- 操作审计日志记录

业务规则:
- 系统保留角色（admin、user）不可删除
- 有用户关联的角色不可删除
- 同名角色不可重复创建
- 同一资源操作组合的权限不可重复创建
"""

import logging
from datetime import datetime

from app.application.errors.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from app.application.services.audit_logger import AuditLogger
from app.domain.models.user import Permission, Role, User
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.domain.repositories.role_repository import PermissionRepository, RoleRepository

logger = logging.getLogger(__name__)

# 系统保留角色，不可删除
SYSTEM_ROLES = {"admin", "user"}


class RoleService:
    """角色和权限管理服务

    提供角色和权限的CRUD操作，以及角色权限关联管理。
    所有操作都会记录审计日志。

    Attributes:
        _role_repo: 角色仓储
        _permission_repo: 权限仓储
        _audit_repo: 审计日志仓储
    """

    def __init__(
        self,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        """初始化角色服务

        Args:
            role_repository: 角色仓储实例
            permission_repository: 权限仓储实例
            audit_log_repository: 审计日志仓储实例
        """
        self._role_repo = role_repository
        self._permission_repo = permission_repository
        self._audit_repo = audit_log_repository

    async def create_role(
        self,
        name: str,
        display_name: str,
        description: str | None,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Role:
        """创建角色

        流程:
        1. 检查角色名是否已存在
        2. 创建角色对象并保存
        3. 记录审计日志

        Args:
            name: 角色标识名（唯一）
            display_name: 角色显示名称
            description: 角色描述
            current_user: 当前操作用户
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Returns:
            创建的角色对象

        Raises:
            ConflictError: 角色名已存在
        """
        if await self._role_repo.exists_by_name(name):
            raise ConflictError(resource="角色", reason="角色名已存在")

        role = Role(
            id=0,
            name=name,
            display_name=display_name,
            description=description,
            created_at=datetime.utcnow(),
        )
        created_role = await self._role_repo.create(role)

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="create_role",
            resource="role",
            resource_id=str(created_role.id),
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"name": name, "display_name": display_name},
        )

        logger.info(f"创建角色成功: name={name}, by={current_user.id}")
        return created_role

    async def update_role(
        self,
        role_id: int,
        display_name: str | None,
        description: str | None,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Role:
        """更新角色信息

        Args:
            role_id: 角色ID
            display_name: 新的显示名称（为None时不更新）
            description: 新的描述（为None时不更新）
            current_user: 当前操作用户
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Returns:
            更新后的角色对象

        Raises:
            NotFoundError: 角色不存在
        """
        role = await self._role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(resource="角色", identifier=str(role_id))

        if display_name is not None:
            role.display_name = display_name
        if description is not None:
            role.description = description

        updated_role = await self._role_repo.update(role)

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="update_role",
            resource="role",
            resource_id=str(role_id),
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "display_name": display_name,
                "description": description,
            },
        )

        logger.info(f"更新角色成功: role_id={role_id}, by={current_user.id}")
        return updated_role

    async def delete_role(
        self,
        role_id: int,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> bool:
        """删除角色

        流程:
        1. 检查角色是否存在
        2. 检查是否为系统保留角色
        3. 检查是否有用户关联
        4. 执行删除并记录审计日志

        Args:
            role_id: 角色ID
            current_user: 当前操作用户
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Returns:
            删除是否成功

        Raises:
            NotFoundError: 角色不存在
            BadRequestError: 系统保留角色或有用户关联
        """
        role = await self._role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(resource="角色", identifier=str(role_id))

        if role.name in SYSTEM_ROLES:
            raise BadRequestError(f"不能删除系统保留角色: {role.name}")

        user_count = await self._role_repo.count_users_with_role(role_id)
        if user_count > 0:
            raise BadRequestError(
                f"角色 {role.name} 仍有 {user_count} 个用户关联，无法删除"
            )

        result = await self._role_repo.delete(role_id)

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="delete_role",
            resource="role",
            resource_id=str(role_id),
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"role_name": role.name},
        )

        logger.info(f"删除角色成功: role_id={role_id}, by={current_user.id}")
        return result

    async def list_all_permissions(self) -> list[Permission]:
        """获取所有权限列表

        Returns:
            系统中所有已定义的权限列表
        """
        return await self._permission_repo.list_all()

    async def create_permission(
        self,
        resource: str,
        action: str,
        display_name: str,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Permission:
        """创建权限

        流程:
        1. 检查权限是否已存在（资源+操作组合唯一）
        2. 创建权限对象并保存
        3. 记录审计日志

        Args:
            resource: 资源类型（如user、role）
            action: 操作类型（如create、read、update、delete）
            display_name: 权限显示名称
            current_user: 当前操作用户
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Returns:
            创建的权限对象

        Raises:
            ConflictError: 权限已存在
        """
        existing = await self._permission_repo.get_by_resource_action(resource, action)
        if existing is not None:
            raise ConflictError(resource="权限", reason=f"{resource}:{action} 已存在")

        permission = Permission(
            id=0,
            resource=resource,
            action=action,
            display_name=display_name,
            created_at=datetime.utcnow(),
        )
        created = await self._permission_repo.create(permission)

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="create_permission",
            resource="permission",
            resource_id=str(created.id),
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "resource": resource,
                "action": action,
                "display_name": display_name,
            },
        )

        logger.info(f"创建权限成功: {resource}:{action}, by={current_user.id}")
        return created

    async def update_permission(
        self,
        permission_id: int,
        display_name: str,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Permission:
        """更新权限信息

        Args:
            permission_id: 权限ID
            display_name: 新的显示名称
            current_user: 当前操作用户
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Returns:
            更新后的权限对象

        Raises:
            NotFoundError: 权限不存在
        """
        permission = await self._permission_repo.get_by_id(permission_id)
        if permission is None:
            raise NotFoundError(resource="权限", identifier=str(permission_id))

        permission.display_name = display_name
        updated = await self._permission_repo.update(permission)
        if updated is None:
            raise NotFoundError(resource="权限", identifier=str(permission_id))

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="update_permission",
            resource="permission",
            resource_id=str(permission_id),
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"display_name": display_name},
        )

        logger.info(
            f"更新权限成功: permission_id={permission_id}, by={current_user.id}"
        )
        return updated

    async def delete_permission(
        self,
        permission_id: int,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> bool:
        """删除权限

        Args:
            permission_id: 权限ID
            current_user: 当前操作用户
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Returns:
            删除是否成功

        Raises:
            NotFoundError: 权限不存在
        """
        permission = await self._permission_repo.get_by_id(permission_id)
        if permission is None:
            raise NotFoundError(resource="权限", identifier=str(permission_id))

        result = await self._permission_repo.delete(permission_id)

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="delete_permission",
            resource="permission",
            resource_id=str(permission_id),
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "resource": permission.resource,
                "action": permission.action,
            },
        )

        logger.info(
            f"删除权限成功: permission_id={permission_id}, by={current_user.id}"
        )
        return result

    async def remove_permission_from_role(
        self,
        role_id: int,
        permission_id: int,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """移除角色的权限

        流程:
        1. 验证角色存在
        2. 验证权限存在
        3. 移除角色与权限的关联
        4. 记录审计日志

        Args:
            role_id: 角色ID
            permission_id: 权限ID
            current_user: 当前操作用户
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Raises:
            NotFoundError: 角色或权限不存在
        """
        role = await self._role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(resource="角色", identifier=str(role_id))

        permission = await self._permission_repo.get_by_id(permission_id)
        if permission is None:
            raise NotFoundError(resource="权限", identifier=str(permission_id))

        await self._permission_repo.remove_permission_from_role(role_id, permission_id)

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="remove_permission",
            resource="role",
            resource_id=str(role_id),
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "role_name": role.name,
                "permission": f"{permission.resource}:{permission.action}",
            },
        )

        logger.info(
            f"移除角色权限成功: role_id={role_id}, permission_id={permission_id}, "
            f"by={current_user.id}"
        )
