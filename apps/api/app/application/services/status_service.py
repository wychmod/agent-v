"""系统状态检查服务模块

本模块提供系统健康状态检查功能，用于监控各依赖服务的运行状态。

主要功能:
- 并发检查多个服务的健康状态
- 聚合多个检查结果
- 异常处理和容错机制

使用场景:
- 健康检查接口 (/health)
- 服务监控和告警
- 运维状态面板
"""

import asyncio

from app.domain.external.health_checker import HealthChecker
from app.domain.models.health_status import HealthStatus


class StatusService:
    """系统状态检查服务

    负责协调多个健康检查器，并发执行检查并聚合结果。
    支持任意数量的健康检查器，检查失败时提供容错处理。

    Attributes:
        _checkers: 健康检查器列表
    """

    def __init__(self, checkers: list[HealthChecker]) -> None:
        """初始化状态服务

        Args:
            checkers: 健康检查器列表，每个检查器负责检查一个服务
        """
        self._checkers = checkers

    async def check_all(self) -> list[HealthStatus]:
        """检查所有服务的健康状态

        流程:
        1. 并发执行所有检查器的检查方法
        2. 捕获并处理检查过程中的异常
        3. 返回所有检查结果（包括失败的检查）

        Returns:
            健康状态列表，每个元素对应一个服务的检查结果
        """
        # 并发执行所有检查，捕获异常避免单个检查失败影响整体
        results = await asyncio.gather(
            *[checker.check() for checker in self._checkers],
            return_exceptions=True,
        )

        processed_results = []
        for result in results:
            if isinstance(result, BaseException):
                # 检查器抛出异常时，返回错误状态
                processed_results.append(
                    HealthStatus(
                        service="未知服务",
                        status="error",
                        details="服务发生未知错误",
                    )
                )
            else:
                processed_results.append(result)
        return processed_results
