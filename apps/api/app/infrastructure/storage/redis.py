"""Redis client module.

提供异步 Redis 客户端的初始化、连接管理和关闭功能。
使用单例模式通过 get_redis_client 函数获取客户端实例。
"""

import logging
from functools import lru_cache
from typing import Self

from redis.asyncio import Redis

from core.config import Settings, get_settings

logger: logging.Logger = logging.getLogger(__name__)


class RedisClient:
    """Redis 异步客户端管理类。

    负责 Redis 连接的初始化、关闭和客户端访问。
    使用内部状态管理连接生命周期，确保线程安全。

    Attributes:
        _client: Redis 客户端实例，未初始化时为 None
        _settings: 应用配置实例
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """初始化 RedisClient 实例。

        Args:
            settings: 配置实例，为 None 时自动获取全局配置
        """
        self._client: Redis | None = None
        self._settings: Settings = settings if settings is not None else get_settings()

    async def init(self) -> None:
        """初始化 Redis 连接。

        创建异步 Redis 连接并验证连接可用性。
        如果已初始化则记录警告并返回。

        Raises:
            ConnectionError: Redis 连接失败时抛出
        """
        if self._client is not None:
            logger.warning("Redis client 已经初始化，跳过重复初始化")
            return

        try:
            self._client = Redis(
                host=self._settings.redis_host,
                port=self._settings.redis_port,
                db=self._settings.redis_db,
                password=self._settings.redis_password,
                decode_responses=True,
            )
            await self._client.ping()  # type: ignore
            logger.info(
                "Redis client 初始化成功: %s:%s/%s",
                self._settings.redis_host,
                self._settings.redis_port,
                self._settings.redis_db,
            )
        except Exception as e:
            logger.error("Redis 初始化失败: %s", e)
            raise ConnectionError(f"无法连接到 Redis: {e}") from e

    async def shutdown(self) -> None:
        """关闭 Redis 连接。

        安全关闭 Redis 连接并清理相关资源。
        同时清除 get_redis_client 的缓存以确保下次获取新实例。
        """
        if self._client is not None:
            try:
                await self._client.aclose()
                logger.info("Redis client 连接已关闭")
            except Exception as e:
                logger.warning("关闭 Redis 连接时发生错误: %s", e)
            finally:
                self._client = None

        get_redis_client.cache_clear()
        logger.debug("Redis client 缓存已清除")

    @property
    def client(self) -> Redis:
        """获取已初始化的 Redis 客户端实例。

        Returns:
            Redis: Redis 客户端实例

        Raises:
            RuntimeError: 如果 Redis 客户端未初始化
        """
        if self._client is None:
            raise RuntimeError("Redis client 未初始化，请先调用 init()")
        return self._client

    async def __aenter__(self) -> Self:
        """异步上下文管理器入口。

        Returns:
            RedisClient: 当前实例
        """
        await self.init()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """异步上下文管理器出口。

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪
        """
        await self.shutdown()


@lru_cache(maxsize=1)
def get_redis_client(settings: Settings | None = None) -> RedisClient:
    """获取 RedisClient 单例实例。

    使用 lru_cache 确保全局只有一个 RedisClient 实例。

    Args:
        settings: 可选的配置实例，用于依赖注入

    Returns:
        RedisClient: Redis 客户端管理实例
    """
    return RedisClient(settings=settings)
