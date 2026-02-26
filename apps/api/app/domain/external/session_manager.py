"""会话管理协议"""

from typing import Protocol

from app.domain.models.user import SessionData


class SessionManager(Protocol):
    """会话管理协议，定义用户会话管理的接口契约"""

    async def create_session(
        self, user_id: str, data: SessionData, ttl: int = 900
    ) -> str:
        """创建会话，返回 session_id"""
        ...

    async def get_session(self, session_id: str) -> SessionData | None:
        """获取会话数据"""
        ...

    async def update_session(
        self, session_id: str, data: SessionData, ttl: int = 900
    ) -> None:
        """更新会话数据"""
        ...

    async def delete_session(self, session_id: str) -> None:
        """删除会话"""
        ...

    async def delete_user_sessions(self, user_id: str) -> int:
        """删除用户所有会话，返回删除的会话数量"""
        ...

    async def extend_session(self, session_id: str, ttl: int = 900) -> None:
        """延长会话过期时间"""
        ...

    async def add_to_blacklist(self, token_jti: str, ttl: int) -> None:
        """将 token 加入黑名单"""
        ...

    async def is_blacklisted(self, token_jti: str) -> bool:
        """检查 token 是否在黑名单中"""
        ...

    async def set_verification_token(
        self, token: str, user_id: str, ttl: int = 900
    ) -> None:
        """存储验证 token（邮箱验证、密码重置）"""
        ...

    async def get_verification_token(self, token: str) -> str | None:
        """获取验证 token 对应的 user_id"""
        ...

    async def delete_verification_token(self, token: str) -> None:
        """删除验证 token"""
        ...
