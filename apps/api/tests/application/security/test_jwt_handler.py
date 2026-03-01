"""JWT 处理器测试

测试 JWT Token 的创建、解码和验证：
- 访问令牌生成与解码
- 刷新令牌生成与解码
- 令牌过期处理
- 错误令牌处理
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.application.errors.exceptions import UnauthorizedError
from app.application.security.jwt_handler import JWTHandler


class TestJWTHandler:
    """JWT 处理器测试"""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """创建 mock 设置"""
        settings = MagicMock()
        settings.jwt_secret_key = "test-secret-key-for-access-token"
        settings.jwt_refresh_secret_key = "test-secret-key-for-refresh-token"
        settings.jwt_algorithm = "HS256"
        settings.jwt_access_token_expire_minutes = 30
        settings.jwt_refresh_token_expire_days = 7
        return settings

    @pytest.fixture
    def handler(self, mock_settings: MagicMock) -> JWTHandler:
        """创建 JWT 处理器实例"""
        return JWTHandler(settings=mock_settings)

    # ==================== Access Token Tests ====================

    def test_create_access_token(self, handler: JWTHandler) -> None:
        """测试创建访问令牌"""
        token = handler.create_access_token(
            user_id="user-123",
            session_id="session-456",
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self, handler: JWTHandler) -> None:
        """测试自定义过期时间的访问令牌"""
        token = handler.create_access_token(
            user_id="user-123",
            expires_delta=timedelta(hours=1),
        )

        payload = handler.decode_access_token(token)
        assert payload["user_id"] == "user-123"

    def test_decode_access_token_valid(self, handler: JWTHandler) -> None:
        """测试解码有效访问令牌"""
        token = handler.create_access_token(
            user_id="user-123",
            session_id="session-456",
        )

        payload = handler.decode_access_token(token)

        assert payload["user_id"] == "user-123"
        assert payload["session_id"] == "session-456"
        assert payload["token_type"] == "access"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_access_token_expired(self, handler: JWTHandler) -> None:
        """测试解码过期访问令牌"""
        token = handler.create_access_token(
            user_id="user-123",
            expires_delta=timedelta(seconds=-1),  # 已过期
        )

        with pytest.raises(UnauthorizedError) as exc_info:
            handler.decode_access_token(token)

        assert "过期" in exc_info.value.message

    def test_decode_access_token_invalid(self, handler: JWTHandler) -> None:
        """测试解码无效访问令牌"""
        with pytest.raises(UnauthorizedError) as exc_info:
            handler.decode_access_token("invalid.token.here")

        assert "无效" in exc_info.value.message

    def test_decode_access_token_wrong_type(self, handler: JWTHandler) -> None:
        """测试使用刷新令牌作为访问令牌"""
        refresh_token = handler.create_refresh_token(user_id="user-123")

        with pytest.raises(UnauthorizedError) as exc_info:
            handler.decode_access_token(refresh_token)

        assert "无效" in exc_info.value.message or "令牌" in exc_info.value.message

    # ==================== Refresh Token Tests ====================

    def test_create_refresh_token(self, handler: JWTHandler) -> None:
        """测试创建刷新令牌"""
        token = handler.create_refresh_token(user_id="user-123")

        assert token is not None
        assert isinstance(token, str)

    def test_decode_refresh_token_valid(self, handler: JWTHandler) -> None:
        """测试解码有效刷新令牌"""
        token = handler.create_refresh_token(user_id="user-123")

        payload = handler.decode_refresh_token(token)

        assert payload["user_id"] == "user-123"
        assert payload["token_type"] == "refresh"

    def test_decode_refresh_token_expired(self, handler: JWTHandler) -> None:
        """测试解码过期刷新令牌"""
        token = handler.create_refresh_token(
            user_id="user-123",
            expires_delta=timedelta(seconds=-1),
        )

        with pytest.raises(UnauthorizedError) as exc_info:
            handler.decode_refresh_token(token)

        assert "过期" in exc_info.value.message

    def test_decode_refresh_token_wrong_type(self, handler: JWTHandler) -> None:
        """测试使用访问令牌作为刷新令牌"""
        access_token = handler.create_access_token(user_id="user-123")

        with pytest.raises(UnauthorizedError) as exc_info:
            handler.decode_refresh_token(access_token)

        assert "无效" in exc_info.value.message or "令牌" in exc_info.value.message

    # ==================== Token Verification Tests ====================

    def test_verify_token_valid(self, handler: JWTHandler) -> None:
        """测试验证有效令牌"""
        token = handler.create_access_token(user_id="user-123")

        assert handler.verify_token(token) is True

    def test_verify_token_invalid(self, handler: JWTHandler) -> None:
        """测试验证无效令牌"""
        assert handler.verify_token("invalid.token") is False

    def test_verify_token_expired(self, handler: JWTHandler) -> None:
        """测试验证过期令牌"""
        token = handler.create_access_token(
            user_id="user-123",
            expires_delta=timedelta(seconds=-1),
        )

        assert handler.verify_token(token) is False

    # ==================== Token Expiry Tests ====================

    def test_get_token_expiry(self, handler: JWTHandler) -> None:
        """测试获取令牌过期时间"""
        token = handler.create_access_token(user_id="user-123")

        expiry = handler.get_token_expiry(token)

        assert expiry is not None
        assert isinstance(expiry, datetime)
        assert expiry > datetime.now(UTC)

    def test_get_token_expiry_invalid(self, handler: JWTHandler) -> None:
        """测试获取无效令牌过期时间"""
        expiry = handler.get_token_expiry("invalid.token")

        assert expiry is None

    def test_get_remaining_ttl(self, handler: JWTHandler) -> None:
        """测试获取令牌剩余有效期"""
        token = handler.create_access_token(
            user_id="user-123",
            expires_delta=timedelta(minutes=10),
        )

        ttl = handler.get_remaining_ttl(token)

        assert ttl > 0
        assert ttl <= 600  # 10 minutes in seconds

    def test_get_remaining_ttl_expired(self, handler: JWTHandler) -> None:
        """测试获取过期令牌剩余有效期"""
        token = handler.create_access_token(
            user_id="user-123",
            expires_delta=timedelta(seconds=-1),
        )

        ttl = handler.get_remaining_ttl(token)

        assert ttl == 0

    def test_get_remaining_ttl_invalid(self, handler: JWTHandler) -> None:
        """测试获取无效令牌剩余有效期"""
        ttl = handler.get_remaining_ttl("invalid.token")

        assert ttl == 0

    # ==================== Verification Token Tests ====================

    def test_create_verification_token(self) -> None:
        """测试创建验证令牌"""
        token = JWTHandler.create_verification_token()

        assert token is not None
        assert isinstance(token, str)
        # UUID 格式
        assert len(token) == 36

    def test_create_verification_token_unique(self) -> None:
        """测试验证令牌唯一性"""
        token1 = JWTHandler.create_verification_token()
        token2 = JWTHandler.create_verification_token()

        assert token1 != token2

    # ==================== Property Tests ====================

    def test_secret_key_property(self, handler: JWTHandler) -> None:
        """测试密钥属性"""
        assert handler.secret_key == "test-secret-key-for-access-token"

    def test_refresh_secret_key_property(self, handler: JWTHandler) -> None:
        """测试刷新令牌密钥属性"""
        assert handler.refresh_secret_key == "test-secret-key-for-refresh-token"

    def test_algorithm_property(self, handler: JWTHandler) -> None:
        """测试算法属性"""
        assert handler.algorithm == "HS256"

    def test_access_token_expire_minutes_property(self, handler: JWTHandler) -> None:
        """测试访问令牌过期时间属性"""
        assert handler.access_token_expire_minutes == 30

    def test_refresh_token_expire_days_property(self, handler: JWTHandler) -> None:
        """测试刷新令牌过期天数属性"""
        assert handler.refresh_token_expire_days == 7

    # ==================== JTI Tests ====================

    def test_access_token_has_unique_jti(self, handler: JWTHandler) -> None:
        """测试访问令牌有唯一 JTI"""
        token1 = handler.create_access_token(user_id="user-123")
        token2 = handler.create_access_token(user_id="user-123")

        payload1 = handler.decode_access_token(token1)
        payload2 = handler.decode_access_token(token2)

        assert payload1["jti"] != payload2["jti"]

    def test_refresh_token_has_unique_jti(self, handler: JWTHandler) -> None:
        """测试刷新令牌有唯一 JTI"""
        token1 = handler.create_refresh_token(user_id="user-123")
        token2 = handler.create_refresh_token(user_id="user-123")

        payload1 = handler.decode_refresh_token(token1)
        payload2 = handler.decode_refresh_token(token2)

        assert payload1["jti"] != payload2["jti"]
