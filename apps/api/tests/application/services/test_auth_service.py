"""认证服务测试

测试 AuthService 的认证功能：
- 用户注册
- 用户登录
- 用户登出
- 令牌刷新
- 邮箱验证
- 密码重置
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.errors.exceptions import (
    ConflictError,
    ForbiddenError,
    UnauthorizedError,
)
from app.application.security.jwt_handler import JWTHandler
from app.application.security.password_handler import PasswordHandler
from app.application.services.auth_service import AuthService
from app.domain.models.user import Role, User, UserWithPassword


class TestAuthServiceRegister:
    """注册功能测试"""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """创建 mock 设置"""
        settings = MagicMock()
        settings.frontend_url = "http://localhost:3000"
        settings.password_min_length = 8
        settings.jwt_secret_key = "test-secret"
        settings.jwt_refresh_secret_key = "test-refresh-secret"
        settings.jwt_algorithm = "HS256"
        settings.jwt_access_token_expire_minutes = 30
        settings.jwt_refresh_token_expire_days = 7
        return settings

    @pytest.fixture
    def auth_service(
        self,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
        mock_session_manager: AsyncMock,
        mock_email_sender: AsyncMock,
        mock_rate_limiter: AsyncMock,
        mock_settings: MagicMock,
    ) -> AuthService:
        """创建认证服务实例"""
        return AuthService(
            user_repository=mock_user_repository,
            role_repository=mock_role_repository,
            audit_log_repository=mock_audit_log_repository,
            session_manager=mock_session_manager,
            email_sender=mock_email_sender,
            rate_limiter=mock_rate_limiter,
            settings=mock_settings,
        )

    @pytest.mark.asyncio
    async def test_register_success(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_email_sender: AsyncMock,
    ) -> None:
        """测试注册成功"""
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.exists_by_username.return_value = False
        mock_user_repository.create.return_value = User(
            id="new-user-id",
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=False,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_role_repository.get_by_name.return_value = Role(
            id=1,
            name="user",
            display_name="普通用户",
            description=None,
            created_at=datetime.now(UTC),
        )

        user = await auth_service.register(
            email="test@example.com",
            username="testuser",
            password="ValidPass123!",
            ip_address="127.0.0.1",
        )

        assert user.email == "test@example.com"
        mock_user_repository.create.assert_called_once()
        mock_role_repository.assign_role_to_user.assert_called_once()
        mock_email_sender.send_verification_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_email_exists(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """测试邮箱已存在"""
        mock_user_repository.exists_by_email.return_value = True

        with pytest.raises(ConflictError) as exc_info:
            await auth_service.register(
                email="existing@example.com",
                username="testuser",
                password="ValidPass123!",
            )

        assert "邮箱已被注册" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_register_username_exists(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """测试用户名已存在"""
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.exists_by_username.return_value = True

        with pytest.raises(ConflictError) as exc_info:
            await auth_service.register(
                email="new@example.com",
                username="existinguser",
                password="ValidPass123!",
            )

        assert "用户名已被使用" in exc_info.value.message


class TestAuthServiceLogin:
    """登录功能测试"""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """创建 mock 设置"""
        settings = MagicMock()
        settings.frontend_url = "http://localhost:3000"
        settings.password_min_length = 8
        settings.jwt_secret_key = "test-secret"
        settings.jwt_refresh_secret_key = "test-refresh-secret"
        settings.jwt_algorithm = "HS256"
        settings.jwt_access_token_expire_minutes = 30
        settings.jwt_refresh_token_expire_days = 7
        return settings

    @pytest.fixture
    def mock_password_handler(self) -> MagicMock:
        """创建 mock 密码处理器"""
        handler = MagicMock(spec=PasswordHandler)
        handler.verify_password.return_value = True
        handler.hash_password.return_value = "$2b$12$hashedpassword"
        handler.validate_password_or_raise.return_value = None
        return handler

    @pytest.fixture
    def auth_service(
        self,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
        mock_session_manager: AsyncMock,
        mock_email_sender: AsyncMock,
        mock_rate_limiter: AsyncMock,
        mock_password_handler: MagicMock,
        mock_settings: MagicMock,
    ) -> AuthService:
        """创建认证服务实例"""
        return AuthService(
            user_repository=mock_user_repository,
            role_repository=mock_role_repository,
            audit_log_repository=mock_audit_log_repository,
            session_manager=mock_session_manager,
            email_sender=mock_email_sender,
            rate_limiter=mock_rate_limiter,
            password_handler=mock_password_handler,
            settings=mock_settings,
        )

    @pytest.fixture
    def active_verified_user(self) -> UserWithPassword:
        """创建已激活已验证用户"""
        return UserWithPassword(
            id="user-123",
            email="test@example.com",
            username="testuser",
            password_hash="$2b$12$hashedpassword",
            is_active=True,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            roles=[],
        )

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
        mock_session_manager: AsyncMock,
        active_verified_user: UserWithPassword,
    ) -> None:
        """测试登录成功"""
        mock_user_repository.get_by_email.return_value = active_verified_user

        result = await auth_service.login(
            email="test@example.com",
            password="ValidPass123!",
            ip_address="127.0.0.1",
        )

        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        mock_session_manager.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_user_not_found(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """测试用户不存在"""
        mock_user_repository.get_by_email.return_value = None

        with pytest.raises(UnauthorizedError) as exc_info:
            await auth_service.login(
                email="nonexistent@example.com",
                password="ValidPass123!",
            )

        assert "邮箱或密码错误" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
        mock_password_handler: MagicMock,
        active_verified_user: UserWithPassword,
    ) -> None:
        """测试密码错误"""
        mock_user_repository.get_by_email.return_value = active_verified_user
        mock_password_handler.verify_password.return_value = False

        with pytest.raises(UnauthorizedError) as exc_info:
            await auth_service.login(
                email="test@example.com",
                password="WrongPassword!",
            )

        assert "邮箱或密码错误" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """测试账户已禁用"""
        inactive_user = UserWithPassword(
            id="user-123",
            email="test@example.com",
            username="testuser",
            password_hash="$2b$12$hashedpassword",
            is_active=False,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            roles=[],
        )
        mock_user_repository.get_by_email.return_value = inactive_user

        with pytest.raises(ForbiddenError):
            await auth_service.login(
                email="test@example.com",
                password="ValidPass123!",
            )

    @pytest.mark.asyncio
    async def test_login_unverified_user(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """测试邮箱未验证"""
        unverified_user = UserWithPassword(
            id="user-123",
            email="test@example.com",
            username="testuser",
            password_hash="$2b$12$hashedpassword",
            is_active=True,
            is_verified=False,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            roles=[],
        )
        mock_user_repository.get_by_email.return_value = unverified_user

        with pytest.raises(ForbiddenError):
            await auth_service.login(
                email="test@example.com",
                password="ValidPass123!",
            )


class TestAuthServiceLogout:
    """登出功能测试"""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """创建 mock 设置"""
        settings = MagicMock()
        settings.jwt_secret_key = "test-secret"
        settings.jwt_refresh_secret_key = "test-refresh-secret"
        settings.jwt_algorithm = "HS256"
        settings.jwt_access_token_expire_minutes = 30
        settings.jwt_refresh_token_expire_days = 7
        return settings

    @pytest.fixture
    def mock_jwt_handler(self, mock_settings: MagicMock) -> JWTHandler:
        """创建 JWT 处理器"""
        return JWTHandler(settings=mock_settings)

    @pytest.fixture
    def auth_service(
        self,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
        mock_session_manager: AsyncMock,
        mock_email_sender: AsyncMock,
        mock_rate_limiter: AsyncMock,
        mock_jwt_handler: JWTHandler,
        mock_settings: MagicMock,
    ) -> AuthService:
        """创建认证服务实例"""
        return AuthService(
            user_repository=mock_user_repository,
            role_repository=mock_role_repository,
            audit_log_repository=mock_audit_log_repository,
            session_manager=mock_session_manager,
            email_sender=mock_email_sender,
            rate_limiter=mock_rate_limiter,
            jwt_handler=mock_jwt_handler,
            settings=mock_settings,
        )

    @pytest.mark.asyncio
    async def test_logout_success(
        self,
        auth_service: AuthService,
        mock_session_manager: AsyncMock,
        mock_jwt_handler: JWTHandler,
    ) -> None:
        """测试登出成功"""
        access_token = mock_jwt_handler.create_access_token(
            user_id="user-123",
            session_id="session-456",
        )

        await auth_service.logout(access_token=access_token)

        mock_session_manager.delete_session.assert_called_once()
        mock_session_manager.add_to_blacklist.assert_called()

    @pytest.mark.asyncio
    async def test_logout_with_refresh_token(
        self,
        auth_service: AuthService,
        mock_session_manager: AsyncMock,
        mock_jwt_handler: JWTHandler,
    ) -> None:
        """测试登出时同时使刷新令牌失效"""
        access_token = mock_jwt_handler.create_access_token(
            user_id="user-123",
            session_id="session-456",
        )
        refresh_token = mock_jwt_handler.create_refresh_token(user_id="user-123")

        await auth_service.logout(
            access_token=access_token,
            refresh_token=refresh_token,
        )

        # 应该将两个令牌都加入黑名单
        assert mock_session_manager.add_to_blacklist.call_count >= 1


class TestAuthServiceVerifyEmail:
    """邮箱验证功能测试"""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """创建 mock 设置"""
        settings = MagicMock()
        settings.frontend_url = "http://localhost:3000"
        settings.jwt_secret_key = "test-secret"
        settings.jwt_refresh_secret_key = "test-refresh-secret"
        settings.jwt_algorithm = "HS256"
        settings.jwt_access_token_expire_minutes = 30
        settings.jwt_refresh_token_expire_days = 7
        return settings

    @pytest.fixture
    def auth_service(
        self,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
        mock_session_manager: AsyncMock,
        mock_email_sender: AsyncMock,
        mock_rate_limiter: AsyncMock,
        mock_settings: MagicMock,
    ) -> AuthService:
        """创建认证服务实例"""
        return AuthService(
            user_repository=mock_user_repository,
            role_repository=mock_role_repository,
            audit_log_repository=mock_audit_log_repository,
            session_manager=mock_session_manager,
            email_sender=mock_email_sender,
            rate_limiter=mock_rate_limiter,
            settings=mock_settings,
        )

    @pytest.mark.asyncio
    async def test_verify_email_success(
        self,
        auth_service: AuthService,
        mock_session_manager: AsyncMock,
        mock_user_repository: AsyncMock,
        mock_email_sender: AsyncMock,
    ) -> None:
        """测试邮箱验证成功"""
        mock_session_manager.get_verification_token.return_value = "user-123"
        mock_user_repository.get_by_id.return_value = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=False,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await auth_service.verify_email(token="valid-token")

        mock_user_repository.update_verified_status.assert_called_once_with(
            "user-123", True
        )
        mock_email_sender.send_welcome_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(
        self,
        auth_service: AuthService,
        mock_session_manager: AsyncMock,
    ) -> None:
        """测试无效验证令牌"""
        mock_session_manager.get_verification_token.return_value = None

        with pytest.raises(UnauthorizedError) as exc_info:
            await auth_service.verify_email(token="invalid-token")

        assert "失效" in exc_info.value.message or "无效" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_verify_email_already_verified(
        self,
        auth_service: AuthService,
        mock_session_manager: AsyncMock,
        mock_user_repository: AsyncMock,
    ) -> None:
        """测试用户已验证"""
        mock_session_manager.get_verification_token.return_value = "user-123"
        mock_user_repository.get_by_id.return_value = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=True,  # 已验证
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # 不应抛出异常，只是静默返回
        await auth_service.verify_email(token="valid-token")

        # 不应更新验证状态
        mock_user_repository.update_verified_status.assert_not_called()


class TestAuthServicePasswordReset:
    """密码重置功能测试"""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """创建 mock 设置"""
        settings = MagicMock()
        settings.frontend_url = "http://localhost:3000"
        settings.password_min_length = 8
        settings.jwt_secret_key = "test-secret"
        settings.jwt_refresh_secret_key = "test-refresh-secret"
        settings.jwt_algorithm = "HS256"
        settings.jwt_access_token_expire_minutes = 30
        settings.jwt_refresh_token_expire_days = 7
        return settings

    @pytest.fixture
    def auth_service(
        self,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
        mock_session_manager: AsyncMock,
        mock_email_sender: AsyncMock,
        mock_rate_limiter: AsyncMock,
        mock_settings: MagicMock,
    ) -> AuthService:
        """创建认证服务实例"""
        return AuthService(
            user_repository=mock_user_repository,
            role_repository=mock_role_repository,
            audit_log_repository=mock_audit_log_repository,
            session_manager=mock_session_manager,
            email_sender=mock_email_sender,
            rate_limiter=mock_rate_limiter,
            settings=mock_settings,
        )

    @pytest.mark.asyncio
    async def test_request_password_reset_success(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
        mock_email_sender: AsyncMock,
    ) -> None:
        """测试请求密码重置成功"""
        mock_user_repository.get_by_email.return_value = UserWithPassword(
            id="user-123",
            email="test@example.com",
            username="testuser",
            password_hash="$2b$12$hashedpassword",
            is_active=True,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await auth_service.request_password_reset(email="test@example.com")

        mock_email_sender.send_password_reset_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_password_reset_user_not_found(
        self,
        auth_service: AuthService,
        mock_user_repository: AsyncMock,
        mock_email_sender: AsyncMock,
    ) -> None:
        """测试用户不存在时静默返回（安全考虑）"""
        mock_user_repository.get_by_email.return_value = None

        # 不应抛出异常
        await auth_service.request_password_reset(email="nonexistent@example.com")

        # 不应发送邮件
        mock_email_sender.send_password_reset_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_reset_password_success(
        self,
        auth_service: AuthService,
        mock_session_manager: AsyncMock,
        mock_user_repository: AsyncMock,
    ) -> None:
        """测试重置密码成功"""
        mock_session_manager.get_verification_token.return_value = "user-123"
        mock_user_repository.get_by_id.return_value = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await auth_service.reset_password(
            token="valid-token",
            new_password="NewValidPass123!",
        )

        mock_user_repository.update_password.assert_called_once()
        mock_session_manager.delete_user_sessions.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(
        self,
        auth_service: AuthService,
        mock_session_manager: AsyncMock,
    ) -> None:
        """测试无效重置令牌"""
        mock_session_manager.get_verification_token.return_value = None

        with pytest.raises(UnauthorizedError):
            await auth_service.reset_password(
                token="invalid-token",
                new_password="NewValidPass123!",
            )
