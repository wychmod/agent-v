"""JWT Token 处理器"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.application.errors.exceptions import UnauthorizedError
from core.config import Settings, get_settings


class JWTHandler:
    """JWT Token 处理器"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def secret_key(self) -> str:
        return self._settings.jwt_secret_key

    @property
    def refresh_secret_key(self) -> str:
        return self._settings.jwt_refresh_secret_key

    @property
    def algorithm(self) -> str:
        return self._settings.jwt_algorithm

    @property
    def access_token_expire_minutes(self) -> int:
        return self._settings.jwt_access_token_expire_minutes

    @property
    def refresh_token_expire_days(self) -> int:
        return self._settings.jwt_refresh_token_expire_days

    def create_access_token(
        self,
        user_id: str,
        session_id: str | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """创建访问令牌"""
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)

        now = datetime.now(UTC)
        expire = now + expires_delta

        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "token_type": "access",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """创建刷新令牌"""
        if expires_delta is None:
            expires_delta = timedelta(days=self.refresh_token_expire_days)

        now = datetime.now(UTC)
        expire = now + expires_delta

        payload = {
            "user_id": user_id,
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "token_type": "refresh",
        }

        return jwt.encode(payload, self.refresh_secret_key, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        """解码访问令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("token_type") != "access":
                raise UnauthorizedError("无效的令牌类型")
            return payload
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("令牌已过期") from None
        except jwt.InvalidTokenError:
            raise UnauthorizedError("无效的令牌") from None

    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        """解码刷新令牌"""
        try:
            payload = jwt.decode(
                token, self.refresh_secret_key, algorithms=[self.algorithm]
            )
            if payload.get("token_type") != "refresh":
                raise UnauthorizedError("无效的令牌类型")
            return payload
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("刷新令牌已过期") from None
        except jwt.InvalidTokenError:
            raise UnauthorizedError("无效的刷新令牌") from None

    def verify_token(self, token: str) -> bool:
        """验证访问令牌是否有效"""
        try:
            self.decode_access_token(token)
            return True
        except UnauthorizedError:
            return False

    def get_token_expiry(self, token: str) -> datetime | None:
        """获取令牌过期时间"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},
            )
            exp = payload.get("exp")
            if exp:
                return datetime.fromtimestamp(exp, tz=UTC)
            return None
        except jwt.InvalidTokenError:
            return None

    def get_remaining_ttl(self, token: str) -> int:
        """获取令牌剩余有效期（秒）"""
        expiry = self.get_token_expiry(token)
        if expiry is None:
            return 0
        remaining = expiry - datetime.now(UTC)
        return max(0, int(remaining.total_seconds()))

    @staticmethod
    def create_verification_token() -> str:
        """创建验证 token（用于邮箱验证、密码重置）"""
        return str(uuid.uuid4())
