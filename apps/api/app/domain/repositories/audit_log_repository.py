"""审计日志仓储协议模块

本模块定义审计日志数据持久化的接口协议。

审计日志用于记录用户操作行为，支持安全审计、
问题追踪和合规性检查等场景。
"""

from datetime import datetime
from typing import Protocol

from app.domain.models.user import AuditLog


class AuditLogRepository(Protocol):
    """审计日志仓储协议

    定义审计日志数据持久化的接口契约。
    支持日志创建、查询和统计功能。
    """

    async def create(self, log: AuditLog) -> AuditLog:
        """创建审计日志

        Args:
            log: 审计日志对象

        Returns:
            创建后的审计日志（含ID）
        """
        ...

    async def get_user_logs(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[AuditLog]:
        """获取用户的操作日志

        Args:
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            审计日志列表
        """
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
        """获取系统审计日志，支持多条件过滤

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            user_id: 用户ID过滤
            action: 操作类型过滤
            resource: 资源类型过滤
            status: 状态过滤
            start_date: 开始时间
            end_date: 结束时间

        Returns:
            审计日志列表
        """
        ...

    async def count_user_logs(self, user_id: str) -> int:
        """统计用户日志数量

        Args:
            user_id: 用户ID

        Returns:
            日志总数
        """
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
        """统计系统日志数量（带过滤条件）

        Args:
            user_id: 用户ID过滤
            action: 操作类型过滤
            resource: 资源类型过滤
            status: 状态过滤
            start_date: 开始时间
            end_date: 结束时间

        Returns:
            符合条件的日志总数
        """
        ...
