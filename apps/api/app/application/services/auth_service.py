"""认证服务"""

import logging
import uuid
from datetime import UTC, datetime

from app.application.errors.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.application.security.jwt_handler import JWTHandler
from app.application.security.password_handler import PasswordHandler
from app.application.security.rate_limiter import RateLimiter
from app.domain.external.email_sender import EmailSender
from app.domain.external.session_manager import SessionManager
from app.domain.models.user import AuditLog, SessionData, User, UserWithPassword
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.domain.repositories.role_repository import RoleRepository
from app.domain.repositories.user_repository import UserRepository
from core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""

    RATE_LIMIT_LOGIN_MAX = 5  # 登录限流最大请求次数
    RATE_LIMIT_LOGIN_WINDOW = 60  # 登录限流时间窗口（秒）
    RATE_LIMIT_REGISTER_MAX = 3  # 注册限流最大请求次数
    RATE_LIMIT_REGISTER_WINDOW = 3600  # 注册限流时间窗口（秒）
    VERIFICATION_TOKEN_TTL = 900  # 验证令牌有效期（秒）
    SESSION_TTL = 900  # 会话有效期（秒）

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        audit_log_repository: AuditLogRepository,
        session_manager: SessionManager,
        email_sender: EmailSender,
        rate_limiter: RateLimiter,
        jwt_handler: JWTHandler | None = None,
        password_handler: PasswordHandler | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._user_repo = user_repository
        self._role_repo = role_repository
        self._audit_repo = audit_log_repository
        self._session_manager = session_manager
        self._email_sender = email_sender
        self._rate_limiter = rate_limiter
        self._jwt_handler = jwt_handler or JWTHandler()
        self._password_handler = password_handler or PasswordHandler()
        self._settings = settings or get_settings()

    async def register(
        self,
        email: str,
        username: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        """用户注册

        流程:
        1. 限流检查：防止恶意批量注册
        2. 密码强度校验
        3. 唯一性检查：邮箱和用户名不能重复
        4. 创建用户：生成密码哈希并入库
        5. 分配默认角色
        6. 发送验证邮件
        7. 记录审计日志
        """
        if ip_address:
            await self._rate_limiter.check_rate_limit_or_raise(
                f"register:{ip_address}",
                self.RATE_LIMIT_REGISTER_MAX,
                self.RATE_LIMIT_REGISTER_WINDOW,
                "注册请求过于频繁，请稍后再试",
            )

        self._password_handler.validate_password_or_raise(password)

        if await self._user_repo.exists_by_email(email):
            raise ConflictError(resource="用户", reason="邮箱已被注册")

        if await self._user_repo.exists_by_username(username):
            raise ConflictError(resource="用户", reason="用户名已被使用")

        password_hash = self._password_handler.hash_password(password)
        user_id = str(uuid.uuid4())

        user_with_password = UserWithPassword(
            id=user_id,
            email=email,
            username=username,
            password_hash=password_hash,
            is_active=True,
            is_verified=False,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        user = await self._user_repo.create(user_with_password)

        default_role = await self._role_repo.get_by_name("user")
        if default_role:
            await self._role_repo.assign_role_to_user(user.id, default_role.id)

        verification_token = JWTHandler.create_verification_token()
        await self._session_manager.set_verification_token(
            verification_token, user.id, self.VERIFICATION_TOKEN_TTL
        )

        verification_url = (
            f"{self._settings.frontend_url}/verify-email?token={verification_token}"
        )
        await self._email_sender.send_verification_email(
            to=email,
            username=username,
            verification_url=verification_url,
        )

        await self._audit_repo.create(
            AuditLog(
                user_id=user.id,
                action="register",
                resource="user",
                resource_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
                details={"email": email, "username": username},
            )
        )

        logger.info(f"用户注册成功: id={user.id}, email={email}")
        return user

    async def login(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        """用户登录

        流程:
        1. 限流检查：防止暴力破解
        2. 验证用户存在性
        3. 验证密码正确性
        4. 检查账户状态（是否激活、是否验证邮箱）
        5. 创建会话并生成令牌
        6. 更新最后登录时间
        7. 记录审计日志
        """
        if ip_address:
            await self._rate_limiter.check_rate_limit_or_raise(
                f"login:{ip_address}",
                self.RATE_LIMIT_LOGIN_MAX,
                self.RATE_LIMIT_LOGIN_WINDOW,
                "登录请求过于频繁，请稍后再试",
            )

        user = await self._user_repo.get_by_email(email)
        if user is None:
            await self._log_failed_login(
                None, email, ip_address, user_agent, "用户不存在"
            )
            raise UnauthorizedError("邮箱或密码错误")

        if not self._password_handler.verify_password(password, user.password_hash):
            await self._log_failed_login(
                user.id, email, ip_address, user_agent, "密码错误"
            )
            raise UnauthorizedError("邮箱或密码错误")

        if not user.is_active:
            await self._log_failed_login(
                user.id, email, ip_address, user_agent, "账户已禁用"
            )
            raise ForbiddenError(resource="用户", action="登录", message="账户已被禁用")

        if not user.is_verified:
            await self._log_failed_login(
                user.id, email, ip_address, user_agent, "邮箱未验证"
            )
            raise ForbiddenError(resource="用户", action="登录", message="邮箱尚未验证")

        session_data = SessionData(
            user_id=user.id,
            roles=[role.name for role in user.roles],
            permissions=user.get_all_permissions(),
            ip_address=ip_address,
            user_agent=user_agent,
            login_at=datetime.now(UTC),
        )
        session_id = await self._session_manager.create_session(
            user.id, session_data, self.SESSION_TTL
        )

        access_token = self._jwt_handler.create_access_token(user.id, session_id)
        refresh_token = self._jwt_handler.create_refresh_token(user.id)

        await self._user_repo.update_last_login(user.id)

        await self._audit_repo.create(
            AuditLog(
                user_id=user.id,
                action="login",
                resource="user",
                resource_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
            )
        )

        logger.info(f"用户登录成功: id={user.id}, email={email}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self._jwt_handler.access_token_expire_minutes * 60,
            "user": User(**user.model_dump(exclude={"password_hash"})),
        }

    async def _log_failed_login(
        self,
        user_id: str | None,
        email: str,
        ip_address: str | None,
        user_agent: str | None,
        reason: str,
    ) -> None:
        """记录登录失败日志"""
        await self._audit_repo.create(
            AuditLog(
                user_id=user_id,
                action="login",
                resource="user",
                ip_address=ip_address,
                user_agent=user_agent,
                status="failed",
                details={"email": email, "reason": reason},
            )
        )

    async def logout(
        self,
        access_token: str,
        refresh_token: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """用户登出

        流程:
        1. 解析 access_token 获取会话信息
        2. 删除服务端会话
        3. 将 access_token 加入黑名单
        4. 如有 refresh_token，一并加入黑名单
        5. 记录审计日志
        """
        try:
            # 处理 access_token
            payload = self._jwt_handler.decode_access_token(access_token)
            user_id = payload.get("user_id")
            session_id = payload.get("session_id")
            access_jti = payload.get("jti")

            if session_id:
                await self._session_manager.delete_session(session_id)

            if access_jti:
                ttl = self._jwt_handler.get_remaining_ttl(access_token)
                if ttl > 0:
                    await self._session_manager.add_to_blacklist(access_jti, ttl)

            # 处理 refresh_token（如提供）
            if refresh_token:
                try:
                    refresh_payload = self._jwt_handler.decode_refresh_token(
                        refresh_token
                    )
                    refresh_jti = refresh_payload.get("jti")
                    if refresh_jti:
                        refresh_ttl = self._jwt_handler.get_remaining_ttl(refresh_token)
                        if refresh_ttl > 0:
                            await self._session_manager.add_to_blacklist(
                                refresh_jti, refresh_ttl
                            )
                except Exception:
                    # refresh_token 解析失败不影响登出流程
                    pass

            await self._audit_repo.create(
                AuditLog(
                    user_id=user_id,
                    action="logout",
                    resource="user",
                    resource_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="success",
                )
            )

            logger.info(f"用户登出成功: user_id={user_id}")
        except Exception as e:
            logger.warning(f"登出处理失败: {e}")

    async def refresh_token(self, refresh_token: str) -> dict:
        """刷新访问令牌

        流程:
        1. 解析刷新令牌
        2. 检查令牌是否在黑名单中
        3. 验证用户状态和存在性
        4. 创建新会话
        5. 生成新的访问令牌
        """
        payload = self._jwt_handler.decode_refresh_token(refresh_token)
        user_id = payload.get("user_id")
        jti = payload.get("jti")

        if not isinstance(user_id, str):
            raise UnauthorizedError("无效的令牌")

        if jti and await self._session_manager.is_blacklisted(jti):
            raise UnauthorizedError("刷新令牌已失效")

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("用户不存在")

        if not user.is_active:
            raise ForbiddenError(
                resource="用户", action="刷新令牌", message="账户已被禁用"
            )

        session_data = SessionData(
            user_id=user.id,
            roles=[role.name for role in user.roles],
            permissions=user.get_all_permissions(),
            ip_address=None,
            user_agent=None,
            login_at=datetime.now(UTC),
        )
        session_id = await self._session_manager.create_session(
            user.id, session_data, self.SESSION_TTL
        )

        access_token = self._jwt_handler.create_access_token(user.id, session_id)

        logger.info(f"刷新令牌成功: user_id={user_id}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self._jwt_handler.access_token_expire_minutes * 60,
        }

    async def verify_email(
        self,
        token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """验证邮箱

        流程:
        1. 验证令牌有效性
        2. 获取用户并检查是否已验证
        3. 更新用户验证状态
        4. 删除验证令牌
        5. 发送欢迎邮件
        6. 记录审计日志
        """
        user_id = await self._session_manager.get_verification_token(token)
        if user_id is None:
            raise UnauthorizedError("验证链接已失效或无效")

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(resource="用户", identifier=user_id)

        if user.is_verified:
            await self._session_manager.delete_verification_token(token)
            return

        await self._user_repo.update_verified_status(user_id, True)
        await self._session_manager.delete_verification_token(token)

        await self._email_sender.send_welcome_email(
            to=user.email,
            username=user.username,
        )

        await self._audit_repo.create(
            AuditLog(
                user_id=user_id,
                action="verify_email",
                resource="user",
                resource_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
            )
        )

        logger.info(f"邮箱验证成功: user_id={user_id}")

    async def request_password_reset(
        self,
        email: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """请求密码重置"""
        user = await self._user_repo.get_by_email(email)
        if user is None:
            return

        reset_token = JWTHandler.create_verification_token()
        await self._session_manager.set_verification_token(
            reset_token, user.id, self.VERIFICATION_TOKEN_TTL
        )

        reset_url = f"{self._settings.frontend_url}/reset-password?token={reset_token}"
        await self._email_sender.send_password_reset_email(
            to=email,
            username=user.username,
            reset_url=reset_url,
        )

        await self._audit_repo.create(
            AuditLog(
                user_id=user.id,
                action="request_password_reset",
                resource="user",
                resource_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
            )
        )

        logger.info(f"密码重置请求成功: user_id={user.id}")

    async def reset_password(
        self,
        token: str,
        new_password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """重置密码

        流程:
        1. 验证重置令牌有效性
        2. 校验新密码强度
        3. 更新用户密码
        4. 删除重置令牌
        5. 使该用户所有会话失效（安全考虑）
        6. 记录审计日志
        """
        user_id = await self._session_manager.get_verification_token(token)
        if user_id is None:
            raise UnauthorizedError("重置链接已失效或无效")

        self._password_handler.validate_password_or_raise(new_password)

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(resource="用户", identifier=user_id)

        password_hash = self._password_handler.hash_password(new_password)
        await self._user_repo.update_password(user_id, password_hash)
        await self._session_manager.delete_verification_token(token)

        await self._session_manager.delete_user_sessions(user_id)

        await self._audit_repo.create(
            AuditLog(
                user_id=user_id,
                action="reset_password",
                resource="user",
                resource_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                status="success",
            )
        )

        logger.info(f"密码重置成功: user_id={user_id}")

    async def verify_access_token(self, token: str) -> User:
        """验证访问令牌并返回用户"""
        payload = self._jwt_handler.decode_access_token(token)
        user_id = payload.get("user_id")
        jti = payload.get("jti")

        if not isinstance(user_id, str):
            raise UnauthorizedError("无效的令牌")

        if jti and await self._session_manager.is_blacklisted(jti):
            raise UnauthorizedError("令牌已失效")

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("用户不存在")

        if not user.is_active:
            raise ForbiddenError(resource="用户", action="访问", message="账户已被禁用")

        return user
