import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.external.health_checker import HealthChecker
from app.domain.models.health_status import HealthStatus

logger = logging.getLogger(__name__)


class MySQLHealthChecker(HealthChecker):
    """MySQL Health Checker"""

    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    async def check(self) -> HealthStatus:
        try:
            await self._db_session.execute(text("SELECT 1"))
            return HealthStatus(service="mysql", status="ok")
        except Exception as e:
            logger.error(f"mysql健康检查失败: {str(e)}")
            return HealthStatus(
                service="mysql",
                status="error",
                details=str(e),
            )
