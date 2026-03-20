"""用户管理服务模块

本模块提供用户账户的完整管理功能。

主要功能:
- 用户信息的查询和更新
- 密码修改
- 用户角色管理（分配、移除）
- 权限检查
- 管理员用户管理（创建、更新、删除）
- 操作审计日志记录

业务规则:
- 用户不能删除自己的账户
- 修改密码需要验证原密码
- 用户名和邮箱全局唯一
- 管理员创建的用户默认已验证
"""

import logging
import uuid
from datetime import datetime

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
    """用户管理服务

    提供用户账户的CRUD操作、角色管理和权限检查功能。
    所有敏感操作都会记录审计日志。

    Attributes:
        _user_repo: 用户仓储
        _role_repo: 角色仓储
        _permission_repo: 权限仓储
        _audit_repo: 审计日志仓储
        _password_handler: 密码处理器
    """

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
        audit_log_repository: AuditLogRepository,
        password_handler: PasswordHandler | None = None,
    ) -> None:
        """初始化用户服务

        Args:
            user_repository: 用户仓储实例
            role_repository: 角色仓储实例
            permission_repository: 权限仓储实例
            audit_log_repository: 审计日志仓储实例
            password_handler: 密码处理器实例，为None时使用默认处理器
        """
        self._user_repo = user_repository
        self._role_repo = role_repository
        self._permission_repo = permission_repository
        self._audit_repo = audit_log_repository
        self._password_handler = password_handler or PasswordHandler()

    async def get_user(self, user_id: str) -> User:
        """获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            用户对象（包含角色和权限信息）

        Raises:
            NotFoundError: 用户不存在
        """
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(resource="用户", identifier=user_id)
        return user

    async def get_user_by_email(self, email: str) -> User:
        """根据邮箱获取用户

        Args:
            email: 用户邮箱

        Returns:
            用户对象（不包含密码哈希）

        Raises:
            NotFoundError: 用户不存在
        """
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
        """更新用户资料

        流程:
        1. 验证用户存在
        2. 检查操作权限（本人或管理员）
        3. 如有用户名更新，检查唯一性
        4. 保存更新并记录审计日志

        Args:
            user_id: 用户ID
            username: 新用户名（为None时不更新）
            current_user: 当前操作用户
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Returns:
            更新后的用户对象

        Raises:
            NotFoundError: 用户不存在
            ForbiddenError: 无权限更新他人资料
            ConflictError: 用户名已被使用
        """
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
        """修改密码

        流程:
        1. 验证用户存在
        2. 验证原密码正确
        3. 验证新密码强度
        4. 更新密码哈希并记录审计日志

        Args:
            user_id: 用户ID
            old_password: 原密码
            new_password: 新密码
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Raises:
            NotFoundError: 用户不存在
            ForbiddenError: 原密码错误
            ValidationError: 新密码强度不足
        """
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
        """获取用户列表

        Args:
            skip: 跳过的记录数（分页用）
            limit: 返回的最大记录数
            is_active: 可选的激活状态过滤条件

        Returns:
            元组 (用户列表, 总数)
        """
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
        """删除用户（软删除）

        流程:
        1. 检查是否尝试删除自己
        2. 验证用户存在
        3. 执行删除并记录审计日志

        Args:
            user_id: 要删除的用户ID
            current_user: 当前操作用户
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Returns:
            删除是否成功

        Raises:
            ForbiddenError: 尝试删除自己
            NotFoundError: 用户不存在
        """
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
        """为用户分配角色

        Args:
            user_id: 用户ID
            role_name: 角色名称
            current_user: 当前操作用户
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Raises:
            NotFoundError: 用户或角色不存在
        """
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
        """移除用户的角色

        Args:
            user_id: 用户ID
            role_name: 角色名称
            current_user: 当前操作用户
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Raises:
            NotFoundError: 用户或角色不存在
        """
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
        """检查用户是否拥有指定权限

        Args:
            user_id: 用户ID
            resource: 资源类型
            action: 操作类型

        Returns:
            True表示有权限，False表示无权限
        """
        return await self._permission_repo.check_user_permission(
            user_id, resource, action
        )

    async def get_user_roles(self, user_id: str) -> list:
        """获取用户的所有角色

        Args:
            user_id: 用户ID

        Returns:
            角色列表
        """
        return await self._role_repo.get_user_roles(user_id)

    async def get_user_permissions(self, user_id: str) -> list:
        """获取用户的所有权限

        Args:
            user_id: 用户ID

        Returns:
            权限列表
        """
        return await self._permission_repo.get_user_permissions(user_id)

    async def list_all_roles(self) -> list:
        """获取所有角色

        Returns:
            系统中所有角色的列表
        """
        return await self._role_repo.list_all()

    async def get_role_permissions(self, role_id: int) -> list:
        """获取角色的所有权限

        Args:
            role_id: 角色ID

        Returns:
            该角色拥有的权限列表
        """
        return await self._permission_repo.get_role_permissions(role_id)

    async def assign_permission_to_role(
        self,
        role_id: int,
        permission_id: int,
        current_user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """为角色分配权限

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
        """管理员创建用户

        流程:
        1. 检查邮箱和用户名唯一性
        2. 验证密码强度
        3. 创建用户（默认已验证邮箱）
        4. 分配默认角色
        5. 记录审计日志

        Args:
            email: 用户邮箱
            username: 用户名
            password: 初始密码
            is_active: 是否激活账户
            must_change_password: 是否需要首次登录修改密码
            current_user: 当前操作的管理员
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Returns:
            创建的用户对象（包含角色信息）

        Raises:
            ConflictError: 邮箱或用户名已存在
            ValidationError: 密码强度不足
        """
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
        """管理员更新用户信息

        流程:
        1. 验证用户存在
        2. 检查用户名和邮箱唯一性（如有更新）
        3. 更新用户信息并记录审计日志

        Args:
            user_id: 用户ID
            username: 新用户名（为None时不更新）
            email: 新邮箱（为None时不更新）
            is_active: 新的激活状态（为None时不更新）
            current_user: 当前操作的管理员
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理

        Returns:
            更新后的用户对象

        Raises:
            NotFoundError: 用户不存在
            ConflictError: 用户名或邮箱已被使用
        """
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
