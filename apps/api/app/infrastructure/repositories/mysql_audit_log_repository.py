"""MySQL审计日志仓储实现模块

本模块实现基于MySQL数据库的审计日志持久化。

使用SQLAlchemy ORM进行数据库操作，支持:
- 审计日志的创建
- 用户日志查询和分页
- 系统日志多条件过滤查询
- 日志统计功能
"""

import logging
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import AuditLog
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.infrastructure.models.user_models import AuditLogModel

logger = logging.getLogger(__name__)


class MySQLAuditLogRepository(AuditLogRepository):
    """MySQL审计日志仓储实现

    将审计日志持久化到MySQL数据库中。

    Attributes:
        _session: SQLAlchemy异步会话
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化审计日志仓储

        Args:
            session: SQLAlchemy异步会话实例
        """
        self._session = session

    def _model_to_audit_log(self, model: AuditLogModel) -> AuditLog:
        """将ORM模型转换为领域模型

        Args:
            model: 审计日志ORM模型

        Returns:
            审计日志领域模型
        """
        return AuditLog(
            id=model.id,
            user_id=model.user_id,
            action=model.action,
            resource=model.resource,
            resource_id=model.resource_id,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            status=model.status,
            details=model.details,
            created_at=model.created_at,
        )

    async def create(self, log: AuditLog) -> AuditLog:
        """创建审计日志"""
        model = AuditLogModel(
            user_id=log.user_id,
            action=log.action,
            resource=log.resource,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            status=log.status,
            details=log.details,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        logger.debug(
            f"创建审计日志: action={model.action}, resource={model.resource}, "
            f"user_id={model.user_id}"
        )
        return self._model_to_audit_log(model)

    async def get_user_logs(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[AuditLog]:
        """获取用户的操作日志"""
        stmt = (
            select(AuditLogModel)
            .where(AuditLogModel.user_id == user_id)
            .order_by(AuditLogModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_audit_log(m) for m in models]

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
        """获取系统审计日志"""
        stmt = select(AuditLogModel)

        if user_id is not None:
            stmt = stmt.where(AuditLogModel.user_id == user_id)
        if action is not None:
            stmt = stmt.where(AuditLogModel.action == action)
        if resource is not None:
            stmt = stmt.where(AuditLogModel.resource == resource)
        if status is not None:
            stmt = stmt.where(AuditLogModel.status == status)
        if start_date is not None:
            stmt = stmt.where(AuditLogModel.created_at >= start_date)
        if end_date is not None:
            stmt = stmt.where(AuditLogModel.created_at <= end_date)

        stmt = stmt.order_by(AuditLogModel.created_at.desc()).offset(skip).limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_audit_log(m) for m in models]

    async def count_user_logs(self, user_id: str) -> int:
        """统计用户日志数量"""
        stmt = select(func.count(AuditLogModel.id)).where(
            AuditLogModel.user_id == user_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

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
        stmt = select(func.count(AuditLogModel.id))

        if user_id is not None:
            stmt = stmt.where(AuditLogModel.user_id == user_id)
        if action is not None:
            stmt = stmt.where(AuditLogModel.action == action)
        if resource is not None:
            stmt = stmt.where(AuditLogModel.resource == resource)
        if status is not None:
            stmt = stmt.where(AuditLogModel.status == status)
        if start_date is not None:
            stmt = stmt.where(AuditLogModel.created_at >= start_date)
        if end_date is not None:
            stmt = stmt.where(AuditLogModel.created_at <= end_date)

        result = await self._session.execute(stmt)
        return result.scalar_one()
