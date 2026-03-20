"""Redis 缓存服务健康检查实现模块

本模块提供 Redis 缓存服务连接健康状态检查功能。

主要功能:
- 检测 Redis 服务连接是否正常
- 返回标准化的健康状态结果

检查方式:
- 使用 Redis PING 命令验证服务连接
- 捕获任何异常并记录错误详情
"""

import logging
from collections.abc import Awaitable
from typing import cast

from app.domain.external.health_checker import HealthChecker
from app.domain.models.health_status import HealthStatus
from app.infrastructure.storage.redis import RedisClient

logger = logging.getLogger(__name__)


class RedisHealthChecker(HealthChecker):
    """Redis 缓存服务健康检查器

    实现 HealthChecker 接口，通过 PING 命令检测 Redis 服务状态。

    Attributes:
        _redis_client: Redis 客户端封装对象
    """

    def __init__(self, redis_client: RedisClient) -> None:
        """初始化 Redis 健康检查器

        Args:
            redis_client: Redis 客户端封装对象
        """
        self._redis_client = redis_client

    async def check(self) -> HealthStatus:
        """执行 Redis 健康检查

        流程:
        1. 向 Redis 服务发送 PING 命令
        2. 收到 PONG 响应则返回 ok 状态
        3. 未收到响应或发生异常则返回 error 状态

        Returns:
            HealthStatus: 包含服务名称、状态和错误详情的健康状态对象
        """
        try:
            # 使用 PING 命令检测 Redis 连接
            # redis-py 的 ping() 类型注解为 Awaitable[bool] | bool，需要 cast 来满足 mypy
            ping_result = await cast(Awaitable[bool], self._redis_client.client.ping())
            if ping_result:
                return HealthStatus(service="redis", status="ok")
            else:
                return HealthStatus(
                    service="redis", status="error", details="Redis服务Ping失败"
                )
        except Exception as e:
            logger.error(f"Redis健康检查失败: {str(e)}")
            return HealthStatus(
                service="redis",
                status="error",
                details=str(e),
            )
