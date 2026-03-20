"""会话管理协议模块

本模块定义用户会话管理的接口协议。

主要功能:
- 会话的创建、读取、更新、删除
- 令牌黑名单管理
- 验证令牌管理（邮箱验证、密码重置）

会话数据通常存储在Redis等高性能缓存中。
"""

from typing import Protocol

from app.domain.models.user import SessionData


class SessionManager(Protocol):
    """会话管理协议

    定义用户会话管理的接口契约。
    支持会话CRUD、令牌黑名单、验证令牌等功能。
    """

    async def create_session(
        self, user_id: str, data: SessionData, ttl: int = 900
    ) -> str:
        """创建会话

        Args:
            user_id: 用户ID
            data: 会话数据
            ttl: 过期时间（秒）

        Returns:
            会话ID
        """
        ...

    async def get_session(self, session_id: str) -> SessionData | None:
        """获取会话数据

        Args:
            session_id: 会话ID

        Returns:
            会话数据，不存在返回None
        """
        ...

    async def update_session(
        self, session_id: str, data: SessionData, ttl: int = 900
    ) -> None:
        """更新会话数据

        Args:
            session_id: 会话ID
            data: 新的会话数据
            ttl: 新的过期时间（秒）
        """
        ...

    async def delete_session(self, session_id: str) -> None:
        """删除会话

        Args:
            session_id: 会话ID
        """
        ...

    async def delete_user_sessions(self, user_id: str) -> int:
        """删除用户所有会话

        用于密码重置后强制登出所有设备。

        Args:
            user_id: 用户ID

        Returns:
            删除的会话数量
        """
        ...

    async def extend_session(self, session_id: str, ttl: int = 900) -> None:
        """延长会话过期时间

        Args:
            session_id: 会话ID
            ttl: 新的过期时间（秒）
        """
        ...

    async def add_to_blacklist(self, token_jti: str, ttl: int) -> None:
        """将令牌加入黑名单

        用于登出时使令牌失效。

        Args:
            token_jti: 令牌的JTI（唯一标识）
            ttl: 黑名单保留时间（应与令牌剩余有效期一致）
        """
        ...

    async def is_blacklisted(self, token_jti: str) -> bool:
        """检查令牌是否在黑名单中

        Args:
            token_jti: 令牌的JTI

        Returns:
            是否在黑名单中
        """
        ...

    async def set_verification_token(
        self, token: str, user_id: str, ttl: int = 900
    ) -> None:
        """存储验证令牌

        用于邮箱验证、密码重置等场景。

        Args:
            token: 验证令牌
            user_id: 关联的用户ID
            ttl: 令牌有效期（秒）
        """
        ...

    async def get_verification_token(self, token: str) -> str | None:
        """获取验证令牌对应的用户ID

        Args:
            token: 验证令牌

        Returns:
            用户ID，令牌无效返回None
        """
        ...

    async def delete_verification_token(self, token: str) -> None:
        """删除验证令牌

        验证成功后调用，防止令牌重复使用。

        Args:
            token: 验证令牌
        """
        ...
