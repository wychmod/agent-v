"""Redis 会话管理实现"""

import logging
import uuid
from collections.abc import Awaitable
from typing import cast

from redis.asyncio import Redis

from app.domain.external.session_manager import SessionManager
from app.domain.models.user import SessionData
from app.infrastructure.storage.redis import RedisClient

logger = logging.getLogger(__name__)


class RedisSessionManager(SessionManager):
    """基于 Redis 的会话管理实现"""

    SESSION_PREFIX = "session:"
    USER_SESSIONS_PREFIX = "user_sessions:"
    BLACKLIST_PREFIX = "blacklist:token:"
    VERIFICATION_PREFIX = "verification:"

    def __init__(self, redis_client: RedisClient) -> None:
        self._redis_client = redis_client

    @property
    def _redis(self) -> Redis:
        return self._redis_client.client

    async def create_session(
        self, user_id: str, data: SessionData, ttl: int = 900
    ) -> str:
        """创建会话，user_sessions_key用于创建不同设备的会话"""
        session_id = str(uuid.uuid4())
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"

        session_data = data.model_dump_json()

        try:
            pipe = self._redis.pipeline()
            pipe.setex(session_key, ttl, session_data)
            pipe.sadd(user_sessions_key, session_id)
            pipe.expire(user_sessions_key, ttl * 2)
            await cast(Awaitable[list], pipe.execute())

            logger.debug(f"创建会话成功: user_id={user_id}, session_id={session_id}")
            return session_id
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            raise

    async def get_session(self, session_id: str) -> SessionData | None:
        """获取会话数据"""
        session_key = f"{self.SESSION_PREFIX}{session_id}"

        try:
            data = await self._redis.get(session_key)
            if data is None:
                return None
            return SessionData.model_validate_json(data)
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None

    async def update_session(
        self, session_id: str, data: SessionData, ttl: int = 900
    ) -> None:
        """更新会话数据"""
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        session_data = data.model_dump_json()

        try:
            await self._redis.setex(session_key, ttl, session_data)
            logger.debug(f"更新会话成功: session_id={session_id}")
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            raise

    async def delete_session(self, session_id: str) -> None:
        """删除会话"""
        session_key = f"{self.SESSION_PREFIX}{session_id}"

        try:
            session_data = await self.get_session(session_id)
            if session_data:
                user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{session_data.user_id}"
                pipe = self._redis.pipeline()
                pipe.delete(session_key)
                pipe.srem(user_sessions_key, session_id)
                await cast(Awaitable[list], pipe.execute())
            else:
                await self._redis.delete(session_key)

            logger.debug(f"删除会话成功: session_id={session_id}")
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            raise

    async def delete_user_sessions(self, user_id: str) -> int:
        """删除用户所有会话"""
        user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"

        try:
            session_ids = await cast(
                Awaitable[set], self._redis.smembers(user_sessions_key)
            )
            if not session_ids:
                return 0

            pipe = self._redis.pipeline()
            for session_id in session_ids:
                session_key = f"{self.SESSION_PREFIX}{session_id}"
                pipe.delete(session_key)
            pipe.delete(user_sessions_key)
            await cast(Awaitable[list], pipe.execute())

            count = len(session_ids)
            logger.info(f"删除用户所有会话: user_id={user_id}, count={count}")
            return count
        except Exception as e:
            logger.error(f"删除用户会话失败: {e}")
            raise

    async def extend_session(self, session_id: str, ttl: int = 900) -> None:
        """延长会话过期时间"""
        session_key = f"{self.SESSION_PREFIX}{session_id}"

        try:
            await self._redis.expire(session_key, ttl)
            logger.debug(f"延长会话过期时间: session_id={session_id}, ttl={ttl}")
        except Exception as e:
            logger.error(f"延长会话过期时间失败: {e}")
            raise

    async def add_to_blacklist(self, token_jti: str, ttl: int) -> None:
        """将 token 加入黑名单"""
        blacklist_key = f"{self.BLACKLIST_PREFIX}{token_jti}"

        try:
            await self._redis.setex(blacklist_key, ttl, "1")
            logger.debug(f"Token 加入黑名单: jti={token_jti}")
        except Exception as e:
            logger.error(f"Token 加入黑名单失败: {e}")
            raise

    async def is_blacklisted(self, token_jti: str) -> bool:
        """检查 token 是否在黑名单中"""
        blacklist_key = f"{self.BLACKLIST_PREFIX}{token_jti}"

        try:
            result = await self._redis.exists(blacklist_key)
            return bool(result)
        except Exception as e:
            logger.error(f"检查黑名单失败: {e}")
            return False

    async def set_verification_token(
        self, token: str, user_id: str, ttl: int = 900
    ) -> None:
        """存储验证 token"""
        verification_key = f"{self.VERIFICATION_PREFIX}{token}"

        try:
            await self._redis.setex(verification_key, ttl, user_id)
            logger.debug(f"存储验证 token: token={token[:8]}...")
        except Exception as e:
            logger.error(f"存储验证 token 失败: {e}")
            raise

    async def get_verification_token(self, token: str) -> str | None:
        """获取验证 token 对应的 user_id"""
        verification_key = f"{self.VERIFICATION_PREFIX}{token}"

        try:
            user_id = await self._redis.get(verification_key)
            return user_id
        except Exception as e:
            logger.error(f"获取验证 token 失败: {e}")
            return None

    async def delete_verification_token(self, token: str) -> None:
        """删除验证 token"""
        verification_key = f"{self.VERIFICATION_PREFIX}{token}"

        try:
            await self._redis.delete(verification_key)
            logger.debug(f"删除验证 token: token={token[:8]}...")
        except Exception as e:
            logger.error(f"删除验证 token 失败: {e}")
            raise
