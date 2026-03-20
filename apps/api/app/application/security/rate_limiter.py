"""请求限流器模块

本模块提供基于Redis的请求限流功能，用于防止API滥用和保护系统资源。

主要功能:
- 基于滑动窗口的请求频率限制
- 支持自定义限流键（按IP、用户ID等维度）
- 提供剩余请求数查询和限流重置功能

使用场景:
- 登录接口防暴力破解
- 注册接口防批量注册
- 敏感操作频率限制
"""

import logging

from redis.asyncio import Redis

from app.application.errors.exceptions import TooManyRequestsError

logger = logging.getLogger(__name__)


class RateLimiter:
    """基于Redis的请求限流器（滑动窗口算法）

    使用Redis的INCR和EXPIRE命令实现简单高效的限流。
    每个限流键在首次计数时设置过期时间，过期后自动重置。

    Attributes:
        _redis: Redis异步客户端实例
    """

    def __init__(self, redis_client: Redis) -> None:
        """初始化限流器

        Args:
            redis_client: Redis异步客户端实例
        """
        self._redis = redis_client

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """检查是否超过限流阈值

        流程:
        1. 对限流键进行原子递增
        2. 如果是首次请求，设置过期时间
        3. 比较当前计数与最大允许数

        Args:
            key: 限流键（如 "login:{ip}" 或 "register:{ip}"）
            max_requests: 时间窗口内允许的最大请求数
            window_seconds: 时间窗口大小（秒）

        Returns:
            True表示未超限可以继续，False表示已超限应拒绝
        """
        rate_key = f"rate_limit:{key}"

        try:
            # 原子递增计数器
            current_count = await self._redis.incr(rate_key)

            # 首次请求时设置过期时间
            if current_count == 1:
                await self._redis.expire(rate_key, window_seconds)

            return current_count <= max_requests
        except Exception as e:
            # Redis异常时放行，避免影响正常业务
            logger.warning(f"限流检查失败: {e}")
            return True

    async def check_rate_limit_or_raise(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        message: str = "请求过于频繁，请稍后再试",
    ) -> None:
        """检查限流，超限则抛出异常

        Args:
            key: 限流键
            max_requests: 时间窗口内允许的最大请求数
            window_seconds: 时间窗口大小（秒）
            message: 超限时的错误提示信息

        Raises:
            TooManyRequestsError: 请求超过限流阈值时抛出
        """
        if not await self.check_rate_limit(key, max_requests, window_seconds):
            raise TooManyRequestsError(message)

    async def get_remaining_requests(
        self,
        key: str,
        max_requests: int,
    ) -> int:
        """获取剩余可用请求数

        Args:
            key: 限流键
            max_requests: 时间窗口内允许的最大请求数

        Returns:
            剩余可用请求数，查询失败时返回最大值
        """
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
        """重置限流计数

        用于管理员手动解除用户限流或测试场景。

        Args:
            key: 限流键
        """
        rate_key = f"rate_limit:{key}"
        try:
            await self._redis.delete(rate_key)
        except Exception as e:
            logger.warning(f"重置限流计数失败: {e}")

    async def get_ttl(self, key: str) -> int:
        """获取限流键的剩余过期时间（秒）

        Args:
            key: 限流键

        Returns:
            剩余过期时间秒数，键不存在或查询失败返回0
        """
        rate_key = f"rate_limit:{key}"
        try:
            ttl = await self._redis.ttl(rate_key)
            return max(0, ttl)
        except Exception as e:
            logger.warning(f"获取限流TTL失败: {e}")
            return 0
