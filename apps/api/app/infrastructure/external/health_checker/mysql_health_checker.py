"""MySQL 数据库健康检查实现模块

本模块提供 MySQL 数据库连接健康状态检查功能。

主要功能:
- 检测 MySQL 数据库连接是否正常
- 返回标准化的健康状态结果

检查方式:
- 执行简单的 "SELECT 1" 查询验证数据库连接
- 捕获任何异常并记录错误详情
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.external.health_checker import HealthChecker
from app.domain.models.health_status import HealthStatus

logger = logging.getLogger(__name__)


class MySQLHealthChecker(HealthChecker):
    """MySQL 数据库健康检查器

    实现 HealthChecker 接口，通过执行测试查询检测数据库连接状态。

    Attributes:
        _db_session: SQLAlchemy 异步数据库会话
    """

    def __init__(self, db_session: AsyncSession) -> None:
        """初始化 MySQL 健康检查器

        Args:
            db_session: SQLAlchemy 异步数据库会话对象
        """
        self._db_session = db_session

    async def check(self) -> HealthStatus:
        """执行 MySQL 健康检查

        流程:
        1. 执行 "SELECT 1" 测试查询
        2. 查询成功则返回 ok 状态
        3. 查询失败则记录错误并返回 error 状态

        Returns:
            HealthStatus: 包含服务名称、状态和错误详情的健康状态对象
        """
        try:
            # 执行简单查询测试数据库连接
            await self._db_session.execute(text("SELECT 1"))
            return HealthStatus(service="mysql", status="ok")
        except Exception as e:
            logger.error(f"mysql健康检查失败: {str(e)}")
            return HealthStatus(
                service="mysql",
                status="error",
                details=str(e),
            )
