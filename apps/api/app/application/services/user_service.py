"""用户管理服务"""

import logging
import uuid

from app.application.errors.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.application.security.password_handler import PasswordHandler
from app.application.services.audit_logger import AuditLogger
from app.domain.models.user import User, UserWithPassword
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.domain.repositories.role_repository import PermissionRepository, RoleRepository
from app.domain.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """用户管理服务"""

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
        audit_log_repository: AuditLogRepository,
        password_handler: PasswordHandler | None = None,
    ) -> None:
        self._user_repo = user_repository
        self._role_repo = role_repository
        self._permission_repo = permission_repository
        self._audit_repo = audit_log_repository
        self._password_handler = password_handler or PasswordHandler()

    async def get_user(self, user_id: str) -> User:
        """获取用户信息"""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(resource="用户", identifier=user_id)
        return user

    async def get_user_by_email(self, email: str) -> User:
        """根据邮箱获取用户"""
        user = await self._user_repo.get_by_email(email)
        if user is None:
            raise NotFoundError(resource="用户", identifier=email)
        return User(**user.model_dump(exclude={"password_hash"}))

    async def update_profile(
        self,
        user_id: str,
        username: str | None = None,
        current_user: User | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        """更新用户资料"""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(resource="用户", identifier=user_id)

        if (
            current_user
            and current_user.id != user_id
            and not current_user.has_role("admin")
        ):
            raise ForbiddenError(resource="用户", action="更新资料")

        if username and username != user.username:
            if await self._user_repo.exists_by_username(username):
                raise ConflictError(resource="用户", reason="用户名已被使用")
            user.username = username

        updated_user = await self._user_repo.update(user)

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="update_profile",
            resource="user",
            resource_id=user_id,
            user_id=current_user.id if current_user else user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"username": username} if username else None,
        )

        logger.info(f"更新用户资料成功: user_id={user_id}")
        return updated_user

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """修改密码"""
        user_data = await self._user_repo.get_by_id(user_id)
        if user_data is None:
            raise NotFoundError(resource="用户", identifier=user_id)

        user = await self._user_repo.get_by_email(user_data.email)
        if user is None:
            raise NotFoundError(resource="用户", identifier=user_id)

        if not self._password_handler.verify_password(old_password, user.password_hash):
            raise ForbiddenError(resource="密码", action="修改", message="原密码错误")

        self._password_handler.validate_password_or_raise(new_password)

        password_hash = self._password_handler.hash_password(new_password)
        await self._user_repo.update_password(user_id, password_hash)

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="change_password",
            resource="user",
            resource_id=user_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info(f"修改密码成功: user_id={user_id}")

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> tuple[list[User], int]:
        """获取用户列表"""
        users = await self._user_repo.list_users(skip, limit, is_active)
        total = await self._user_repo.count(is_active)
        return users, total

    async def delete_user(
        self,
        user_id: str,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> bool:
        """删除用户（软删除）"""
        if user_id == current_user.id:
            raise ForbiddenError(
                resource="用户", action="删除", message="不能删除自己的账户"
            )

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(resource="用户", identifier=user_id)

        result = await self._user_repo.delete(user_id)

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="delete_user",
            resource="user",
            resource_id=user_id,
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"deleted_user_email": user.email},
        )

        logger.info(f"删除用户成功: user_id={user_id}, by={current_user.id}")
        return result

    async def assign_role(
        self,
        user_id: str,
        role_name: str,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """为用户分配角色"""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(resource="用户", identifier=user_id)

        role = await self._role_repo.get_by_name(role_name)
        if role is None:
            raise NotFoundError(resource="角色", identifier=role_name)

        await self._role_repo.assign_role_to_user(user_id, role.id, current_user.id)

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="assign_role",
            resource="user",
            resource_id=user_id,
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"role_name": role_name},
        )

        logger.info(
            f"分配角色成功: user_id={user_id}, role={role_name}, by={current_user.id}"
        )

    async def remove_role(
        self,
        user_id: str,
        role_name: str,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """移除用户的角色"""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(resource="用户", identifier=user_id)

        role = await self._role_repo.get_by_name(role_name)
        if role is None:
            raise NotFoundError(resource="角色", identifier=role_name)

        await self._role_repo.remove_role_from_user(user_id, role.id)

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="remove_role",
            resource="user",
            resource_id=user_id,
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"role_name": role_name},
        )

        logger.info(
            f"移除角色成功: user_id={user_id}, role={role_name}, by={current_user.id}"
        )

    async def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """检查用户是否拥有指定权限"""
        return await self._permission_repo.check_user_permission(
            user_id, resource, action
        )

    async def get_user_roles(self, user_id: str) -> list:
        """获取用户的所有角色"""
        return await self._role_repo.get_user_roles(user_id)

    async def get_user_permissions(self, user_id: str) -> list:
        """获取用户的所有权限"""
        return await self._permission_repo.get_user_permissions(user_id)

    async def list_all_roles(self) -> list:
        """获取所有角色"""
        return await self._role_repo.list_all()

    async def get_role_permissions(self, role_id: int) -> list:
        """获取角色的所有权限"""
        return await self._permission_repo.get_role_permissions(role_id)

    async def assign_permission_to_role(
        self,
        role_id: int,
        permission_id: int,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """为角色分配权限"""
        role = await self._role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(resource="角色", identifier=str(role_id))

        permission = await self._permission_repo.get_by_id(permission_id)
        if permission is None:
            raise NotFoundError(resource="权限", identifier=str(permission_id))

        await self._permission_repo.assign_permission_to_role(role_id, permission_id)

        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="assign_permission",
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
            f"分配权限成功: role_id={role_id}, permission_id={permission_id}, "
            f"by={current_user.id}"
        )

    async def create_user_by_admin(
        self,
        email: str,
        username: str,
        password: str,
        is_active: bool = True,
        must_change_password: bool = False,
        current_user: User | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        """管理员创建用户"""
        # 检查邮箱唯一性
        if await self._user_repo.exists_by_email(email):
            raise ConflictError(resource="用户", reason="邮箱已被注册")

        # 检查用户名唯一性
        if await self._user_repo.exists_by_username(username):
            raise ConflictError(resource="用户", reason="用户名已被使用")

        # 验证密码强度
        self._password_handler.validate_password_or_raise(password)

        # 生成密码哈希
        password_hash = self._password_handler.hash_password(password)

        from datetime import datetime

        # 创建用户
        user = UserWithPassword(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            password_hash=password_hash,
            is_active=is_active,
            is_verified=True,  # 管理员创建的用户直接验证
            must_change_password=must_change_password,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        created_user = await self._user_repo.create(user)

        # 分配默认角色
        default_role = await self._role_repo.get_by_name("user")
        if default_role:
            await self._role_repo.assign_role_to_user(
                created_user.id,
                default_role.id,
                current_user.id if current_user else None,
            )

        # 记录审计日志
        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="admin_create_user",
            resource="user",
            resource_id=created_user.id,
            user_id=current_user.id if current_user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "email": email,
                "username": username,
                "is_active": is_active,
                "must_change_password": must_change_password,
            },
        )

        logger.info(
            f"管理员创建用户成功: user_id={created_user.id}, "
            f"by={current_user.id if current_user else 'system'}"
        )

        # 重新获取用户以加载角色信息
        result_user = await self._user_repo.get_by_id(created_user.id)
        if result_user is None:
            raise NotFoundError(resource="用户", identifier=created_user.id)
        return result_user

    async def update_user_by_admin(
        self,
        user_id: str,
        username: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        current_user: User | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        """管理员更新用户信息"""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(resource="用户", identifier=user_id)

        changes: dict[str, str | bool] = {}

        # 更新用户名
        if username is not None and username != user.username:
            if await self._user_repo.exists_by_username(username):
                raise ConflictError(resource="用户", reason="用户名已被使用")
            user.username = username
            changes["username"] = username

        # 更新邮箱
        if email is not None and email != user.email:
            if await self._user_repo.exists_by_email(email):
                raise ConflictError(resource="用户", reason="邮箱已被注册")
            user.email = email
            changes["email"] = email

        # 更新激活状态
        if is_active is not None and is_active != user.is_active:
            user.is_active = is_active
            changes["is_active"] = is_active

        # 保存更新
        updated_user = await self._user_repo.update(user)

        # 记录审计日志
        await AuditLogger.log_success(
            audit_repo=self._audit_repo,
            action="admin_update_user",
            resource="user",
            resource_id=user_id,
            user_id=current_user.id if current_user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            details=changes,
        )

        logger.info(
            f"管理员更新用户成功: user_id={user_id}, "
            f"changes={changes}, "
            f"by={current_user.id if current_user else 'system'}"
        )

        return updated_user
