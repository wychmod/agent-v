"""请求限流器"""

import logging

from redis.asyncio import Redis

from app.application.errors.exceptions import TooManyRequestsError

logger = logging.getLogger(__name__)


class RateLimiter:
    """基于 Redis 的请求限流器（滑动窗口算法）"""

    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """检查是否超过限流阈值

        Args:
            key: 限流键（如 "login:{ip}" 或 "register:{ip}"）
            max_requests: 时间窗口内允许的最大请求数
            window_seconds: 时间窗口大小（秒）

        Returns:
            True 表示未超限，False 表示已超限
        """
        rate_key = f"rate_limit:{key}"

        try:
            current_count = await self._redis.incr(rate_key)

            if current_count == 1:
                await self._redis.expire(rate_key, window_seconds)

            return current_count <= max_requests
        except Exception as e:
            logger.warning(f"限流检查失败: {e}")
            return True

    async def check_rate_limit_or_raise(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        message: str = "请求过于频繁，请稍后再试",
    ) -> None:
        """检查限流，超限则抛出异常"""
        if not await self.check_rate_limit(key, max_requests, window_seconds):
            raise TooManyRequestsError(message)

    async def get_remaining_requests(
        self,
        key: str,
        max_requests: int,
    ) -> int:
        """获取剩余可用请求数"""
        rate_key = f"rate_limit:{key}"

        try:
            current_count = await self._redis.get(rate_key)
            if current_count is None:
                return max_requests
            return max(0, max_requests - int(current_count))
        except Exception as e:
            logger.warning(f"获取剩余请求数失败: {e}")
            return max_requests

    async def reset_rate_limit(self, key: str) -> None:
        """重置限流计数"""
        rate_key = f"rate_limit:{key}"
        try:
            await self._redis.delete(rate_key)
        except Exception as e:
            logger.warning(f"重置限流计数失败: {e}")

    async def get_ttl(self, key: str) -> int:
        """获取限流键的剩余过期时间（秒）"""
        rate_key = f"rate_limit:{key}"
        try:
            ttl = await self._redis.ttl(rate_key)
            return max(0, ttl)
        except Exception as e:
            logger.warning(f"获取限流TTL失败: {e}")
            return 0
