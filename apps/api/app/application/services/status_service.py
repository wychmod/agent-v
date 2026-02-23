import asyncio

from app.domain.external.health_checker import HealthChecker
from app.domain.models.health_status import HealthStatus


class StatusService:
    """状态服务：检查状态"""

    def __init__(self, checkers: list[HealthChecker]) -> None:
        """构造函数，传递所有检查器完成服务初始化"""
        self._checkers = checkers

    async def check_all(self) -> list[HealthStatus]:
        """检查所有服务状态"""
        results = await asyncio.gather(
            *[checker.check() for checker in self._checkers],
            return_exceptions=True,
        )
        processed_results = []
        for result in results:
            if isinstance(result, BaseException):
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
