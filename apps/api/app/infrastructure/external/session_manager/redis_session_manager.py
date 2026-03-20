"""Redis 会话管理服务实现模块

本模块提供基于 Redis 的会话管理功能实现，支持用户会话的完整生命周期管理。

主要功能:
- 会话创建、获取、更新、删除
- 用户多设备会话管理
- 会话过期时间管理
- Token 黑名单管理
- 验证 Token 存储管理

存储结构:
- session:{session_id} -> SessionData JSON 字符串
- user_sessions:{user_id} -> Set[session_id] 用户会话集合
- blacklist:token:{jti} -> "1" 黑名单标记
- verification:{token} -> user_id 验证 Token 映射

技术特点:
- 使用 Redis Pipeline 实现原子性批量操作
- 支持多设备同时登录（不同会话ID）
- 自动过期清理，无需定期任务
"""

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
    """基于 Redis 的会话管理服务实现

    实现 SessionManager 接口，提供高性能的会话管理功能。
    使用 Redis 的键过期特性自动清理过期会话。

    Attributes:
        SESSION_PREFIX: 会话数据键前缀
        USER_SESSIONS_PREFIX: 用户会话集合键前缀
        BLACKLIST_PREFIX: Token 黑名单键前缀
        VERIFICATION_PREFIX: 验证 Token 键前缀
    """

    SESSION_PREFIX = "session:"
    USER_SESSIONS_PREFIX = "user_sessions:"
    BLACKLIST_PREFIX = "blacklist:token:"
    VERIFICATION_PREFIX = "verification:"

    def __init__(self, redis_client: RedisClient) -> None:
        """初始化 Redis 会话管理器

        Args:
            redis_client: Redis 客户端封装对象
        """
        self._redis_client = redis_client

    @property
    def _redis(self) -> Redis:
        """获取底层 Redis 客户端实例"""
        return self._redis_client.client

    async def create_session(
        self, user_id: str, data: SessionData, ttl: int = 900
    ) -> str:
        """创建用户会话

        流程:
        1. 生成唯一会话 ID（UUID4）
        2. 构建会话键和用户会话集合键
        3. 使用 Pipeline 原子性执行:
           - 存储会话数据（带过期时间）
           - 将会话 ID 加入用户会话集合
           - 设置用户会话集合过期时间

        Args:
            user_id: 用户唯一标识
            data: 会话数据对象
            ttl: 会话过期时间（秒），默认 900 秒（15分钟）

        Returns:
            str: 新创建的会话 ID

        Raises:
            Exception: Redis 操作失败时抛出

        Note:
            user_sessions_key 用于支持同一用户在不同设备的多会话管理
        """
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
        """获取会话数据

        Args:
            session_id: 会话唯一标识

        Returns:
            SessionData | None: 会话数据对象，不存在时返回 None
        """
        session_key = f"{self.SESSION_PREFIX}{session_id}"

        try:
            data = await self._redis.get(session_key)
            if data is None:
                return None
            # 反序列化 JSON 数据为 SessionData 对象
            return SessionData.model_validate_json(data)
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None

    async def update_session(
        self, session_id: str, data: SessionData, ttl: int = 900
    ) -> None:
        """更新会话数据

        用新数据覆盖现有会话，并重置过期时间。

        Args:
            session_id: 会话唯一标识
            data: 新的会话数据对象
            ttl: 新的过期时间（秒），默认 900 秒

        Raises:
            Exception: Redis 操作失败时抛出
        """
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        session_data = data.model_dump_json()

        try:
            await self._redis.setex(session_key, ttl, session_data)
            logger.debug(f"更新会话成功: session_id={session_id}")
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            raise

    async def delete_session(self, session_id: str) -> None:
        """删除指定会话

        流程:
        1. 获取会话数据以获取用户 ID
        2. 如果会话存在，使用 Pipeline 原子删除:
           - 删除会话数据
           - 从用户会话集合中移除
        3. 如果会话不存在，直接尝试删除键

        Args:
            session_id: 会话唯一标识

        Raises:
            Exception: Redis 操作失败时抛出
        """
        session_key = f"{self.SESSION_PREFIX}{session_id}"

        try:
            # 获取会话数据以获取用户ID
            session_data = await self.get_session(session_id)
            if session_data:
                user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{session_data.user_id}"
                # 使用 Pipeline 原子删除会话和更新用户会话集合
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
        """删除用户的所有会话

        用于用户登出所有设备或账户安全操作时清除所有会话。

        流程:
        1. 获取用户会话集合中的所有会话 ID
        2. 如果没有会话，直接返回 0
        3. 使用 Pipeline 批量删除所有会话键和用户会话集合

        Args:
            user_id: 用户唯一标识

        Returns:
            int: 被删除的会话数量

        Raises:
            Exception: Redis 操作失败时抛出
        """
        user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"

        try:
            # 获取用户所有会话 ID
            session_ids = await cast(
                Awaitable[set], self._redis.smembers(user_sessions_key)
            )
            if not session_ids:
                return 0

            # 批量删除所有会话
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
        """延长会话过期时间

        用于用户活动时刷新会话，防止活跃用户被登出。

        Args:
            session_id: 会话唯一标识
            ttl: 新的过期时间（秒），默认 900 秒

        Raises:
            Exception: Redis 操作失败时抛出
        """
        session_key = f"{self.SESSION_PREFIX}{session_id}"

        try:
            await self._redis.expire(session_key, ttl)
            logger.debug(f"延长会话过期时间: session_id={session_id}, ttl={ttl}")
        except Exception as e:
            logger.error(f"延长会话过期时间失败: {e}")
            raise

    async def add_to_blacklist(self, token_jti: str, ttl: int) -> None:
        """将 Token 加入黑名单

        用于登出时使 JWT Token 失效，防止已登出的 Token 继续使用。

        Args:
            token_jti: JWT Token 的唯一标识（jti claim）
            ttl: 黑名单过期时间（秒），应与 Token 过期时间一致

        Raises:
            Exception: Redis 操作失败时抛出
        """
        blacklist_key = f"{self.BLACKLIST_PREFIX}{token_jti}"

        try:
            await self._redis.setex(blacklist_key, ttl, "1")
            logger.debug(f"Token 加入黑名单: jti={token_jti}")
        except Exception as e:
            logger.error(f"Token 加入黑名单失败: {e}")
            raise

    async def is_blacklisted(self, token_jti: str) -> bool:
        """检查 Token 是否在黑名单中

        Args:
            token_jti: JWT Token 的唯一标识（jti claim）

        Returns:
            bool: Token 在黑名单中返回 True，否则返回 False
        """
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
        """存储验证 Token

        用于邮箱验证、密码重置等场景的临时 Token 存储。

        Args:
            token: 验证 Token 字符串
            user_id: 关联的用户 ID
            ttl: 过期时间（秒），默认 900 秒（15分钟）

        Raises:
            Exception: Redis 操作失败时抛出
        """
        verification_key = f"{self.VERIFICATION_PREFIX}{token}"

        try:
            await self._redis.setex(verification_key, ttl, user_id)
            logger.debug(f"存储验证 token: token={token[:8]}...")
        except Exception as e:
            logger.error(f"存储验证 token 失败: {e}")
            raise

    async def get_verification_token(self, token: str) -> str | None:
        """获取验证 Token 对应的用户 ID

        Args:
            token: 验证 Token 字符串

        Returns:
            str | None: 关联的用户 ID，Token 不存在或已过期时返回 None
        """
        verification_key = f"{self.VERIFICATION_PREFIX}{token}"

        try:
            user_id = await self._redis.get(verification_key)
            return user_id
        except Exception as e:
            logger.error(f"获取验证 token 失败: {e}")
            return None

    async def delete_verification_token(self, token: str) -> None:
        """删除验证 Token

        验证完成后应删除 Token，防止重复使用。

        Args:
            token: 验证 Token 字符串

        Raises:
            Exception: Redis 操作失败时抛出
        """
        verification_key = f"{self.VERIFICATION_PREFIX}{token}"

        try:
            await self._redis.delete(verification_key)
            logger.debug(f"删除验证 token: token={token[:8]}...")
        except Exception as e:
            logger.error(f"删除验证 token 失败: {e}")
            raise
