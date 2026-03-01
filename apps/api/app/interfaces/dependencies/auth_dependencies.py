"""认证依赖注入"""

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

security = HTTPBearer(auto_error=False)


@lru_cache
def get_jwt_handler() -> JWTHandler:
    """获取 JWT 处理器单例"""
    return JWTHandler()


@lru_cache
def get_password_handler() -> PasswordHandler:
    """获取密码处理器单例"""
    return PasswordHandler()


def get_rate_limiter() -> RateLimiter:
    """获取限流器"""
    redis_client = get_redis_client()
    return RateLimiter(redis_client.client)


def get_session_manager() -> RedisSessionManager:
    """获取会话管理器"""
    redis_client = get_redis_client()
    return RedisSessionManager(redis_client)


@lru_cache
def get_email_sender() -> SMTPEmailSender:
    """获取邮件发送器单例"""
    return SMTPEmailSender()


async def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthService:
    """获取认证服务"""
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
    """获取用户服务"""
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
    """获取角色权限服务"""
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
    """获取当前登录用户"""
    if credentials is None:
        raise UnauthorizedError("未提供认证令牌")

    token = credentials.credentials
    return await auth_service.verify_access_token(token)


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """获取当前激活的用户"""
    if not current_user.is_active:
        raise ForbiddenError(resource="用户", action="访问", message="账户已被禁用")
    return current_user


def require_roles(*roles: str) -> Callable:
    """要求用户拥有指定角色之一"""

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        for role in roles:
            if current_user.has_role(role):
                return current_user
        raise ForbiddenError(resource="用户", action="访问", message="权限不足")

    return role_checker


def require_permission(resource: str, action: str) -> Callable:
    """要求用户拥有指定权限"""

    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.has_permission(resource, action):
            return current_user
        raise ForbiddenError(resource=resource, action=action, message="权限不足")

    return permission_checker


def get_client_ip(request: Request) -> str | None:
    """获取客户端 IP 地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_user_agent(
    user_agent: Annotated[str | None, Header(alias="User-Agent")] = None,
) -> str | None:
    """获取用户代理"""
    return user_agent
