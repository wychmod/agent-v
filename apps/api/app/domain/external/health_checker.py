"""健康检查协议模块

本模块定义服务健康检查的接口协议。

用于监控依赖服务（数据库、缓存等）的运行状态，
支持系统健康检查接口的实现。
"""

from typing import Protocol

from app.domain.models.health_status import HealthStatus


class HealthChecker(Protocol):
    """服务健康检查协议

    定义健康检查的接口契约。
    每个实现类负责检查一个特定服务的健康状态。
    """

    async def check(self) -> HealthStatus:
        """检查服务健康状态

        Returns:
            健康状态对象，包含服务名、状态和详情
        """
        ...
