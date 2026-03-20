"""MySQL用户仓储实现模块

本模块实现基于MySQL数据库的用户数据持久化。

使用SQLAlchemy ORM进行数据库操作，支持:
- 用户的创建、查询、更新
- 密码和登录时间更新
- 用户列表分页查询
- 邮箱和用户名唯一性检查
"""

import logging
from datetime import datetime
from typing import cast

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.user import Permission, Role, User, UserWithPassword
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.models.user_models import (
    RoleModel,
    RolePermissionModel,
    UserModel,
    UserRoleModel,
)

logger = logging.getLogger(__name__)


class MySQLUserRepository(UserRepository):
    """MySQL用户仓储实现

    将用户数据持久化到MySQL数据库中。
    自动加载用户的角色和权限信息。

    Attributes:
        _session: SQLAlchemy异步会话
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化用户仓储

        Args:
            session: SQLAlchemy异步会话实例
        """
        self._session = session

    def _model_to_user(self, model: UserModel) -> User:
        """将ORM模型转换为领域模型

        自动加载关联的角色和权限信息。

        Args:
            model: 用户ORM模型

        Returns:
            用户领域模型
        """
        roles = []
        for user_role in model.roles:
            role_model = user_role.role
            permissions = []
            for role_perm in role_model.permissions:
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
            roles.append(
                Role(
                    id=role_model.id,
                    name=role_model.name,
                    display_name=role_model.display_name,
                    description=role_model.description,
                    created_at=role_model.created_at,
                    permissions=permissions,
                )
            )

        return User(
            id=model.id,
            email=model.email,
            username=model.username,
            is_active=model.is_active,
            is_verified=model.is_verified,
            must_change_password=model.must_change_password,
            last_login_at=model.last_login_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            roles=roles,
        )

    def _model_to_user_with_password(self, model: UserModel) -> UserWithPassword:
        """将 ORM 模型转换为包含密码的领域模型"""
        user = self._model_to_user(model)
        return UserWithPassword(
            **user.model_dump(),
            password_hash=model.password_hash,
        )

    async def create(self, user: UserWithPassword) -> User:
        """创建新用户"""
        model = UserModel(
            id=user.id,
            email=user.email,
            username=user.username,
            password_hash=user.password_hash,
            is_active=user.is_active,
            is_verified=user.is_verified,
            must_change_password=user.must_change_password,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        logger.info(f"创建用户成功: id={model.id}, email={model.email}")
        return self._model_to_user(model)

    async def get_by_id(self, user_id: str) -> User | None:
        """根据 ID 获取用户"""
        stmt = (
            select(UserModel)
            .options(
                selectinload(UserModel.roles)
                .selectinload(UserRoleModel.role)
                .selectinload(RoleModel.permissions)
                .selectinload(RolePermissionModel.permission)
            )
            .where(UserModel.id == user_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None
        return self._model_to_user(model)

    async def get_by_email(self, email: str) -> UserWithPassword | None:
        """根据邮箱获取用户（含密码哈希）"""
        stmt = (
            select(UserModel)
            .options(
                selectinload(UserModel.roles)
                .selectinload(UserRoleModel.role)
                .selectinload(RoleModel.permissions)
                .selectinload(RolePermissionModel.permission)
            )
            .where(UserModel.email == email)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None
        return self._model_to_user_with_password(model)

    async def get_by_username(self, username: str) -> User | None:
        """根据用户名获取用户"""
        stmt = (
            select(UserModel)
            .options(
                selectinload(UserModel.roles)
                .selectinload(UserRoleModel.role)
                .selectinload(RoleModel.permissions)
                .selectinload(RolePermissionModel.permission)
            )
            .where(UserModel.username == username)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None
        return self._model_to_user(model)

    async def update(self, user: User) -> User:
        """更新用户信息"""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user.id)
            .values(
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                is_verified=user.is_verified,
                must_change_password=user.must_change_password,
                updated_at=datetime.utcnow(),
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

        logger.info(f"更新用户成功: id={user.id}")
        updated_user = await self.get_by_id(user.id)
        assert updated_user is not None, f"更新后用户不存在: id={user.id}"
        return updated_user

    async def update_password(self, user_id: str, password_hash: str) -> None:
        """更新用户密码"""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                password_hash=password_hash,
                must_change_password=False,
                updated_at=datetime.utcnow(),
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()
        logger.info(f"更新用户密码成功: id={user_id}")

    async def update_last_login(self, user_id: str) -> None:
        """更新最后登录时间"""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(last_login_at=datetime.utcnow())
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def update_verified_status(self, user_id: str, is_verified: bool) -> None:
        """更新邮箱验证状态"""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                is_verified=is_verified,
                updated_at=datetime.utcnow(),
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()
        logger.info(f"更新邮箱验证状态: id={user_id}, is_verified={is_verified}")

    async def delete(self, user_id: str) -> bool:
        """软删除用户"""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                is_active=False,
                updated_at=datetime.utcnow(),
            )
        )
        result = cast(CursorResult, await self._session.execute(stmt))
        await self._session.flush()
        logger.info(f"软删除用户: id={user_id}")
        return result.rowcount > 0

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> list[User]:
        """分页查询用户列表"""
        stmt = (
            select(UserModel)
            .options(
                selectinload(UserModel.roles)
                .selectinload(UserRoleModel.role)
                .selectinload(RoleModel.permissions)
                .selectinload(RolePermissionModel.permission)
            )
            .order_by(UserModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        if is_active is not None:
            stmt = stmt.where(UserModel.is_active == is_active)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_user(m) for m in models]

    async def count(self, is_active: bool | None = None) -> int:
        """统计用户数量"""
        stmt = select(func.count(UserModel.id))
        if is_active is not None:
            stmt = stmt.where(UserModel.is_active == is_active)

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def exists_by_email(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        stmt = select(func.count(UserModel.id)).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def exists_by_username(self, username: str) -> bool:
        """检查用户名是否已存在"""
        stmt = select(func.count(UserModel.id)).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0
