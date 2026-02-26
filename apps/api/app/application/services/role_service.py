"""角色和权限管理服务"""

import logging

from app.application.errors.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from app.domain.models.user import AuditLog, Permission, Role, User
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.domain.repositories.role_repository import PermissionRepository, RoleRepository

logger = logging.getLogger(__name__)

SYSTEM_ROLES = {"admin", "user"}


class RoleService:
    """角色和权限管理服务"""

    def __init__(
        self,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
        audit_log_repository: AuditLogRepository,
    ) -> None:
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
        """创建角色"""
        if await self._role_repo.exists_by_name(name):
            raise ConflictError(resource="角色", reason="角色名已存在")

        from datetime import datetime

        role = Role(
            id=0,
            name=name,
            display_name=display_name,
            description=description,
            created_at=datetime.utcnow(),
        )
        created_role = await self._role_repo.create(role)

        await self._audit_repo.create(
            AuditLog(
                user_id=current_user.id,
                action="create_role",
                resource="role",
                resource_id=str(created_role.id),
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
                details={"name": name, "display_name": display_name},
            )
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
        """更新角色"""
        role = await self._role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(resource="角色", identifier=str(role_id))

        if display_name is not None:
            role.display_name = display_name
        if description is not None:
            role.description = description

        updated_role = await self._role_repo.update(role)

        await self._audit_repo.create(
            AuditLog(
                user_id=current_user.id,
                action="update_role",
                resource="role",
                resource_id=str(role_id),
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
                details={
                    "display_name": display_name,
                    "description": description,
                },
            )
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
        """删除角色"""
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

        await self._audit_repo.create(
            AuditLog(
                user_id=current_user.id,
                action="delete_role",
                resource="role",
                resource_id=str(role_id),
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
                details={"role_name": role.name},
            )
        )

        logger.info(f"删除角色成功: role_id={role_id}, by={current_user.id}")
        return result

    async def list_all_permissions(self) -> list[Permission]:
        """获取所有权限"""
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
        """创建权限"""
        existing = await self._permission_repo.get_by_resource_action(resource, action)
        if existing is not None:
            raise ConflictError(resource="权限", reason=f"{resource}:{action} 已存在")

        from datetime import datetime

        permission = Permission(
            id=0,
            resource=resource,
            action=action,
            display_name=display_name,
            created_at=datetime.utcnow(),
        )
        created = await self._permission_repo.create(permission)

        await self._audit_repo.create(
            AuditLog(
                user_id=current_user.id,
                action="create_permission",
                resource="permission",
                resource_id=str(created.id),
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
                details={
                    "resource": resource,
                    "action": action,
                    "display_name": display_name,
                },
            )
        )

        logger.info(
            f"创建权限成功: {resource}:{action}, by={current_user.id}"
        )
        return created

    async def update_permission(
        self,
        permission_id: int,
        display_name: str,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Permission:
        """更新权限"""
        permission = await self._permission_repo.get_by_id(permission_id)
        if permission is None:
            raise NotFoundError(resource="权限", identifier=str(permission_id))

        permission.display_name = display_name
        updated = await self._permission_repo.update(permission)

        await self._audit_repo.create(
            AuditLog(
                user_id=current_user.id,
                action="update_permission",
                resource="permission",
                resource_id=str(permission_id),
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
                details={"display_name": display_name},
            )
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
        """删除权限"""
        permission = await self._permission_repo.get_by_id(permission_id)
        if permission is None:
            raise NotFoundError(resource="权限", identifier=str(permission_id))

        result = await self._permission_repo.delete(permission_id)

        await self._audit_repo.create(
            AuditLog(
                user_id=current_user.id,
                action="delete_permission",
                resource="permission",
                resource_id=str(permission_id),
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
                details={
                    "resource": permission.resource,
                    "action": permission.action,
                },
            )
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
        """移除角色的权限"""
        role = await self._role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(resource="角色", identifier=str(role_id))

        permission = await self._permission_repo.get_by_id(permission_id)
        if permission is None:
            raise NotFoundError(resource="权限", identifier=str(permission_id))

        await self._permission_repo.remove_permission_from_role(role_id, permission_id)

        await self._audit_repo.create(
            AuditLog(
                user_id=current_user.id,
                action="remove_permission",
                resource="role",
                resource_id=str(role_id),
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
                details={
                    "role_name": role.name,
                    "permission": f"{permission.resource}:{permission.action}",
                },
            )
        )

        logger.info(
            f"移除角色权限成功: role_id={role_id}, permission_id={permission_id}, "
            f"by={current_user.id}"
        )
