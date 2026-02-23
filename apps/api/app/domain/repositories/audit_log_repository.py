"""审计日志仓储协议"""

from datetime import datetime
from typing import Protocol

from app.domain.models.user import AuditLog


class AuditLogRepository(Protocol):
    """审计日志仓储协议，定义审计日志数据持久化的接口契约"""

    async def create(self, log: AuditLog) -> AuditLog:
        """创建审计日志"""
        ...

    async def get_user_logs(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[AuditLog]:
        """获取用户的操作日志"""
        ...

    async def get_system_logs(
        self,
        skip: int = 0,
        limit: int = 20,
        user_id: str | None = None,
        action: str | None = None,
        resource: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[AuditLog]:
        """获取系统审计日志，支持多条件过滤"""
        ...

    async def count_user_logs(self, user_id: str) -> int:
        """统计用户日志数量"""
        ...

    async def count_system_logs(
        self,
        user_id: str | None = None,
        action: str | None = None,
        resource: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """统计系统日志数量"""
        ...
