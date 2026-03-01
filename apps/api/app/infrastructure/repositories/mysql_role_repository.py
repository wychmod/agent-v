"""MySQL 角色和权限仓储实现"""

import logging
from typing import cast

from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.errors.exceptions import ServerInternalError
from app.domain.models.user import Permission, Role
from app.domain.repositories.role_repository import PermissionRepository, RoleRepository
from app.infrastructure.models.user_models import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserRoleModel,
)

logger = logging.getLogger(__name__)


class MySQLRoleRepository(RoleRepository):
    """MySQL 角色仓储实现"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _model_to_role(
        self, model: RoleModel, include_permissions: bool = True
    ) -> Role:
        """将 ORM 模型转换为领域模型"""
        permissions = []
        if include_permissions:
            for role_perm in model.permissions:
                perm_model = role_perm.permission
                permissions.append(
                    Permission(
                        id=perm_model.id,
                        resource=perm_model.resource,
                        action=perm_model.action,
                        display_name=perm_model.display_name,
                        created_at=perm_model.created_at,
                    )
                )

        return Role(
            id=model.id,
            name=model.name,
            display_name=model.display_name,
            description=model.description,
            created_at=model.created_at,
            permissions=permissions,
        )

    async def create(self, role: Role) -> Role:
        """创建新角色"""
        model = RoleModel(
            name=role.name,
            display_name=role.display_name,
            description=role.description,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        logger.info(f"创建角色成功: id={model.id}, name={model.name}")
        return self._model_to_role(model, include_permissions=False)

    async def get_by_id(self, role_id: int) -> Role | None:
        """根据 ID 获取角色"""
        stmt = (
            select(RoleModel)
            .options(
                selectinload(RoleModel.permissions).selectinload(
                    RolePermissionModel.permission
                )
            )
            .where(RoleModel.id == role_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None
        return self._model_to_role(model)

    async def get_by_name(self, name: str) -> Role | None:
        """根据名称获取角色"""
        stmt = (
            select(RoleModel)
            .options(
                selectinload(RoleModel.permissions).selectinload(
                    RolePermissionModel.permission
                )
            )
            .where(RoleModel.name == name)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None
        return self._model_to_role(model)

    async def list_all(self) -> list[Role]:
        """获取所有角色"""
        stmt = (
            select(RoleModel)
            .options(
                selectinload(RoleModel.permissions).selectinload(
                    RolePermissionModel.permission
                )
            )
            .order_by(RoleModel.id)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_role(m) for m in models]

    async def get_user_roles(self, user_id: str) -> list[Role]:
        """获取用户的所有角色"""
        stmt = (
            select(RoleModel)
            .join(UserRoleModel)
            .options(
                selectinload(RoleModel.permissions).selectinload(
                    RolePermissionModel.permission
                )
            )
            .where(UserRoleModel.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_role(m) for m in models]

    async def assign_role_to_user(
        self, user_id: str, role_id: int, assigned_by: str | None = None
    ) -> None:
        """为用户分配角色"""
        exists_stmt = select(func.count(UserRoleModel.id)).where(
            UserRoleModel.user_id == user_id, UserRoleModel.role_id == role_id
        )
        result = await self._session.execute(exists_stmt)
        if result.scalar_one() > 0:
            logger.debug(f"用户已拥有该角色: user_id={user_id}, role_id={role_id}")
            return

        model = UserRoleModel(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
        )
        self._session.add(model)
        await self._session.flush()
        logger.info(
            f"分配角色成功: user_id={user_id}, role_id={role_id}, assigned_by={assigned_by}"
        )

    async def remove_role_from_user(self, user_id: str, role_id: int) -> None:
        """移除用户的角色"""
        stmt = delete(UserRoleModel).where(
            UserRoleModel.user_id == user_id, UserRoleModel.role_id == role_id
        )
        await self._session.execute(stmt)
        await self._session.flush()
        logger.info(f"移除角色成功: user_id={user_id}, role_id={role_id}")

    async def user_has_role(self, user_id: str, role_name: str) -> bool:
        """检查用户是否拥有指定角色"""
        stmt = (
            select(func.count(UserRoleModel.id))
            .join(RoleModel)
            .where(UserRoleModel.user_id == user_id, RoleModel.name == role_name)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def update(self, role: Role) -> Role:
        """更新角色信息"""
        stmt = (
            update(RoleModel)
            .where(RoleModel.id == role.id)
            .values(
                display_name=role.display_name,
                description=role.description,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()
        logger.info(f"更新角色成功: id={role.id}")
        updated_role = await self.get_by_id(role.id)
        if updated_role is None:
            raise ServerInternalError(message=f"更新后无法找到角色: id={role.id}")
        return updated_role

    async def delete(self, role_id: int) -> bool:
        """删除角色"""
        stmt = delete(RolePermissionModel).where(RolePermissionModel.role_id == role_id)
        await self._session.execute(stmt)

        stmt = delete(RoleModel).where(RoleModel.id == role_id)
        result = cast(CursorResult, await self._session.execute(stmt))
        await self._session.flush()
        logger.info(f"删除角色: id={role_id}")
        return result.rowcount > 0

    async def exists_by_name(self, name: str) -> bool:
        """检查角色名是否已存在"""
        stmt = select(func.count(RoleModel.id)).where(RoleModel.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def count_users_with_role(self, role_id: int) -> int:
        """统计拥有该角色的用户数"""
        stmt = select(func.count(UserRoleModel.id)).where(
            UserRoleModel.role_id == role_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()


class MySQLPermissionRepository(PermissionRepository):
    """MySQL 权限仓储实现"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _model_to_permission(self, model: PermissionModel) -> Permission:
        """将 ORM 模型转换为领域模型"""
        return Permission(
            id=model.id,
            resource=model.resource,
            action=model.action,
            display_name=model.display_name,
            created_at=model.created_at,
        )

    async def create(self, permission: Permission) -> Permission:
        """创建新权限"""
        model = PermissionModel(
            resource=permission.resource,
            action=permission.action,
            display_name=permission.display_name,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        logger.info(
            f"创建权限成功: id={model.id}, resource={model.resource}, action={model.action}"
        )
        return self._model_to_permission(model)

    async def get_by_id(self, permission_id: int) -> Permission | None:
        """根据 ID 获取权限"""
        stmt = select(PermissionModel).where(PermissionModel.id == permission_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None
        return self._model_to_permission(model)

    async def get_by_resource_action(
        self, resource: str, action: str
    ) -> Permission | None:
        """根据资源和操作获取权限"""
        stmt = select(PermissionModel).where(
            PermissionModel.resource == resource, PermissionModel.action == action
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None
        return self._model_to_permission(model)

    async def list_all(self) -> list[Permission]:
        """获取所有权限"""
        stmt = select(PermissionModel).order_by(
            PermissionModel.resource, PermissionModel.action
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_permission(m) for m in models]

    async def get_role_permissions(self, role_id: int) -> list[Permission]:
        """获取角色的所有权限"""
        stmt = (
            select(PermissionModel)
            .join(RolePermissionModel)
            .where(RolePermissionModel.role_id == role_id)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_permission(m) for m in models]

    async def get_user_permissions(self, user_id: str) -> list[Permission]:
        """获取用户的所有权限（通过角色）"""
        stmt = (
            select(PermissionModel)
            .join(RolePermissionModel)
            .join(RoleModel)
            .join(UserRoleModel)
            .where(UserRoleModel.user_id == user_id)
            .distinct()
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_permission(m) for m in models]

    async def assign_permission_to_role(self, role_id: int, permission_id: int) -> None:
        """为角色分配权限"""
        exists_stmt = select(func.count(RolePermissionModel.id)).where(
            RolePermissionModel.role_id == role_id,
            RolePermissionModel.permission_id == permission_id,
        )
        result = await self._session.execute(exists_stmt)
        if result.scalar_one() > 0:
            logger.debug(
                f"角色已拥有该权限: role_id={role_id}, permission_id={permission_id}"
            )
            return

        model = RolePermissionModel(
            role_id=role_id,
            permission_id=permission_id,
        )
        self._session.add(model)
        await self._session.flush()
        logger.info(f"分配权限成功: role_id={role_id}, permission_id={permission_id}")

    async def remove_permission_from_role(
        self, role_id: int, permission_id: int
    ) -> None:
        """移除角色的权限"""
        stmt = delete(RolePermissionModel).where(
            RolePermissionModel.role_id == role_id,
            RolePermissionModel.permission_id == permission_id,
        )
        await self._session.execute(stmt)
        await self._session.flush()
        logger.info(f"移除权限成功: role_id={role_id}, permission_id={permission_id}")

    async def check_user_permission(
        self, user_id: str, resource: str, action: str
    ) -> bool:
        """检查用户是否拥有指定权限"""
        stmt = (
            select(func.count(PermissionModel.id))
            .join(RolePermissionModel)
            .join(RoleModel)
            .join(UserRoleModel)
            .where(
                UserRoleModel.user_id == user_id,
                PermissionModel.resource == resource,
                PermissionModel.action == action,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def update(self, permission: Permission) -> Permission | None:
        """更新权限信息"""
        stmt = (
            update(PermissionModel)
            .where(PermissionModel.id == permission.id)
            .values(display_name=permission.display_name)
        )
        await self._session.execute(stmt)
        await self._session.flush()
        logger.info(f"更新权限成功: id={permission.id}")
        return await self.get_by_id(permission.id)

    async def delete(self, permission_id: int) -> bool:
        """删除权限"""
        stmt = delete(RolePermissionModel).where(
            RolePermissionModel.permission_id == permission_id
        )
        await self._session.execute(stmt)

        stmt = delete(PermissionModel).where(PermissionModel.id == permission_id)
        result = cast(CursorResult, await self._session.execute(stmt))
        await self._session.flush()
        logger.info(f"删除权限: id={permission_id}")
        return result.rowcount > 0
