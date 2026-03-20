"""认证依赖注入模块

本模块提供 FastAPI 路由所需的认证相关依赖项。

主要功能:
- 安全组件单例获取（JWT处理器、密码处理器、限流器等）
- 服务层依赖注入（认证服务、用户服务、角色服务）
- 用户认证与授权（当前用户获取、角色检查、权限检查）
- 请求信息提取（客户端IP、User-Agent）

依赖项说明:
- get_jwt_handler: JWT 令牌处理器
- get_password_handler: 密码加密处理器
- get_rate_limiter: 请求限流器
- get_session_manager: Redis 会话管理器
- get_email_sender: SMTP 邮件发送器
- get_auth_service: 认证服务
- get_user_service: 用户管理服务
- get_role_service: 角色权限服务
- get_current_user: 当前登录用户
- get_current_active_user: 当前激活用户
- require_roles: 角色要求装饰器
- require_permission: 权限要求装饰器
"""

import logging
from collections.abc import Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.errors.exceptions import ForbiddenError, UnauthorizedError
from app.application.security.jwt_handler import JWTHandler
from app.application.security.password_handler import PasswordHandler
from app.application.security.rate_limiter import RateLimiter
from app.application.services.auth_service import AuthService
from app.application.services.role_service import RoleService
from app.application.services.user_service import UserService
from app.domain.models.user import User
from app.infrastructure.external.email_sender.smtp_email_sender import SMTPEmailSender
from app.infrastructure.external.session_manager.redis_session_manager import (
    RedisSessionManager,
)
from app.infrastructure.repositories.mysql_audit_log_repository import (
    MySQLAuditLogRepository,
)
from app.infrastructure.repositories.mysql_role_repository import (
    MySQLPermissionRepository,
    MySQLRoleRepository,
)
from app.infrastructure.repositories.mysql_user_repository import MySQLUserRepository
from app.infrastructure.storage.mysql import get_db_session
from app.infrastructure.storage.redis import get_redis_client

logger = logging.getLogger(__name__)

# HTTP Bearer 认证方案，auto_error=False 允许未认证请求通过（由后续代码处理）
security = HTTPBearer(auto_error=False)


@lru_cache
def get_jwt_handler() -> JWTHandler:
    """获取 JWT 处理器单例

    Returns:
        JWTHandler: JWT 令牌处理器实例
    """
    return JWTHandler()


@lru_cache
def get_password_handler() -> PasswordHandler:
    """获取密码处理器单例

    Returns:
        PasswordHandler: 密码加密处理器实例
    """
    return PasswordHandler()


def get_rate_limiter() -> RateLimiter:
    """获取限流器实例

    Returns:
        RateLimiter: 基于 Redis 的请求限流器
    """
    redis_client = get_redis_client()
    return RateLimiter(redis_client.client)


def get_session_manager() -> RedisSessionManager:
    """获取会话管理器实例

    Returns:
        RedisSessionManager: 基于 Redis 的会话管理器
    """
    redis_client = get_redis_client()
    return RedisSessionManager(redis_client)


@lru_cache
def get_email_sender() -> SMTPEmailSender:
    """获取邮件发送器单例

    Returns:
        SMTPEmailSender: SMTP 邮件发送器实例
    """
    return SMTPEmailSender()


async def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthService:
    """获取认证服务实例

    组装认证服务所需的所有依赖组件。

    Args:
        session: 数据库会话

    Returns:
        AuthService: 完整配置的认证服务实例
    """
    user_repo = MySQLUserRepository(session)
    role_repo = MySQLRoleRepository(session)
    audit_repo = MySQLAuditLogRepository(session)
    session_manager = get_session_manager()
    email_sender = get_email_sender()
    rate_limiter = get_rate_limiter()

    return AuthService(
        user_repository=user_repo,
        role_repository=role_repo,
        audit_log_repository=audit_repo,
        session_manager=session_manager,
        email_sender=email_sender,
        rate_limiter=rate_limiter,
    )


async def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserService:
    """获取用户管理服务实例

    Args:
        session: 数据库会话

    Returns:
        UserService: 用户管理服务实例
    """
    user_repo = MySQLUserRepository(session)
    role_repo = MySQLRoleRepository(session)
    permission_repo = MySQLPermissionRepository(session)
    audit_repo = MySQLAuditLogRepository(session)

    return UserService(
        user_repository=user_repo,
        role_repository=role_repo,
        permission_repository=permission_repo,
        audit_log_repository=audit_repo,
    )


async def get_role_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RoleService:
    """获取角色权限服务实例

    Args:
        session: 数据库会话

    Returns:
        RoleService: 角色权限服务实例
    """
    role_repo = MySQLRoleRepository(session)
    permission_repo = MySQLPermissionRepository(session)
    audit_repo = MySQLAuditLogRepository(session)

    return RoleService(
        role_repository=role_repo,
        permission_repository=permission_repo,
        audit_log_repository=audit_repo,
    )


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """获取当前登录用户

    从请求头中提取 JWT 令牌并验证，返回对应的用户对象。

    Args:
        request: FastAPI 请求对象
        credentials: HTTP Bearer 认证凭据
        auth_service: 认证服务

    Returns:
        User: 当前登录的用户对象

    Raises:
        UnauthorizedError: 未提供认证令牌时抛出
    """
    if credentials is None:
        raise UnauthorizedError("未提供认证令牌")

    token = credentials.credentials
    return await auth_service.verify_access_token(token)


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """获取当前激活的用户

    在 get_current_user 基础上额外检查用户是否处于激活状态。

    Args:
        current_user: 当前登录用户

    Returns:
        User: 当前激活的用户对象

    Raises:
        ForbiddenError: 用户账户被禁用时抛出
    """
    if not current_user.is_active:
        raise ForbiddenError(resource="用户", action="访问", message="账户已被禁用")
    return current_user


def require_roles(*roles: str) -> Callable:
    """创建角色要求依赖项

    返回一个依赖函数，检查用户是否拥有指定角色之一。

    Args:
        *roles: 允许访问的角色名称列表

    Returns:
        Callable: FastAPI 依赖函数

    Example:
        @router.get("/admin")
        async def admin_route(
            user: Annotated[User, Depends(require_roles("admin"))]
        ):
            ...
    """

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        """检查用户角色"""
        for role in roles:
            if current_user.has_role(role):
                return current_user
        raise ForbiddenError(resource="用户", action="访问", message="权限不足")

    return role_checker


def require_permission(resource: str, action: str) -> Callable:
    """创建权限要求依赖项

    返回一个依赖函数，检查用户是否拥有指定资源的操作权限。

    Args:
        resource: 资源名称
        action: 操作类型

    Returns:
        Callable: FastAPI 依赖函数
    """

    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        """检查用户权限"""
        if current_user.has_permission(resource, action):
            return current_user
        raise ForbiddenError(resource=resource, action=action, message="权限不足")

    return permission_checker


def get_client_ip(request: Request) -> str | None:
    """获取客户端 IP 地址

    优先从 X-Forwarded-For 头获取（支持反向代理），
    否则从请求客户端直接获取。

    Args:
        request: FastAPI 请求对象

    Returns:
        str | None: 客户端 IP 地址，无法获取时返回 None
    """
    # 检查代理头（适用于 Nginx 等反向代理场景）
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_user_agent(
    user_agent: Annotated[str | None, Header(alias="User-Agent")] = None,
) -> str | None:
    """获取用户代理字符串

    Args:
        user_agent: 从请求头提取的 User-Agent

    Returns:
        str | None: User-Agent 字符串
    """
    return user_agent
