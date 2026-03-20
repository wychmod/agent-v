"""JWT令牌处理器模块

本模块提供JWT（JSON Web Token）的创建、解析和验证功能，
用于实现用户身份认证和会话管理。

主要功能:
- 创建访问令牌（Access Token）和刷新令牌（Refresh Token）
- 解码和验证JWT令牌
- 获取令牌过期时间和剩余有效期
- 生成验证令牌（用于邮箱验证、密码重置等场景）

令牌类型说明:
- access: 访问令牌，有效期短（默认15分钟），用于API请求认证
- refresh: 刷新令牌，有效期长（默认7天），用于获取新的访问令牌
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.application.errors.exceptions import UnauthorizedError
from core.config import Settings, get_settings


class JWTHandler:
    """JWT令牌处理器

    负责JWT令牌的生成、解析和验证工作。
    使用HS256算法进行签名，支持访问令牌和刷新令牌两种类型。

    Attributes:
        _settings: 应用配置实例，包含JWT相关的密钥和过期时间配置
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """初始化JWT处理器

        Args:
            settings: 可选的配置实例，为None时使用全局配置
        """
        self._settings = settings or get_settings()

    @property
    def secret_key(self) -> str:
        """获取访问令牌的签名密钥"""
        return self._settings.jwt_secret_key

    @property
    def refresh_secret_key(self) -> str:
        """获取刷新令牌的签名密钥"""
        return self._settings.jwt_refresh_secret_key

    @property
    def algorithm(self) -> str:
        """获取JWT签名算法"""
        return self._settings.jwt_algorithm

    @property
    def access_token_expire_minutes(self) -> int:
        """获取访问令牌过期时间（分钟）"""
        return self._settings.jwt_access_token_expire_minutes

    @property
    def refresh_token_expire_days(self) -> int:
        """获取刷新令牌过期时间（天）"""
        return self._settings.jwt_refresh_token_expire_days

    def create_access_token(
        self,
        user_id: str,
        session_id: str | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """创建访问令牌

        流程:
        1. 计算令牌过期时间
        2. 构建令牌载荷（包含用户ID、会话ID、过期时间等）
        3. 使用密钥签名生成JWT字符串

        Args:
            user_id: 用户唯一标识
            session_id: 可选的会话ID，用于服务端会话管理
            expires_delta: 自定义过期时间间隔，为None时使用默认配置

        Returns:
            编码后的JWT字符串
        """
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
        """创建刷新令牌

        流程:
        1. 计算令牌过期时间（默认7天）
        2. 构建令牌载荷
        3. 使用刷新令牌专用密钥签名

        Args:
            user_id: 用户唯一标识
            expires_delta: 自定义过期时间间隔，为None时使用默认配置

        Returns:
            编码后的JWT刷新令牌字符串
        """
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
        """解码访问令牌

        流程:
        1. 使用密钥解码JWT
        2. 验证令牌类型是否为access
        3. 返回解码后的载荷数据

        Args:
            token: JWT访问令牌字符串

        Returns:
            解码后的令牌载荷字典，包含user_id、session_id、exp等字段

        Raises:
            UnauthorizedError: 令牌无效、已过期或类型不匹配时抛出
        """
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
        """解码刷新令牌

        流程:
        1. 使用刷新令牌专用密钥解码JWT
        2. 验证令牌类型是否为refresh
        3. 返回解码后的载荷数据

        Args:
            token: JWT刷新令牌字符串

        Returns:
            解码后的令牌载荷字典，包含user_id、exp等字段

        Raises:
            UnauthorizedError: 令牌无效、已过期或类型不匹配时抛出
        """
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
        """验证访问令牌是否有效

        Args:
            token: JWT访问令牌字符串

        Returns:
            True表示令牌有效，False表示令牌无效或已过期
        """
        try:
            self.decode_access_token(token)
            return True
        except UnauthorizedError:
            return False

    def get_token_expiry(self, token: str) -> datetime | None:
        """获取令牌过期时间

        Args:
            token: JWT令牌字符串

        Returns:
            令牌的过期时间（UTC时区），解析失败返回None
        """
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
        """获取令牌剩余有效期（秒）

        Args:
            token: JWT令牌字符串

        Returns:
            剩余有效期秒数，已过期或无效返回0
        """
        expiry = self.get_token_expiry(token)
        if expiry is None:
            return 0
        remaining = expiry - datetime.now(UTC)
        return max(0, int(remaining.total_seconds()))

    @staticmethod
    def create_verification_token() -> str:
        """创建验证令牌（用于邮箱验证、密码重置）

        Returns:
            随机生成的UUID字符串，作为一次性验证令牌
        """
        return str(uuid.uuid4())
