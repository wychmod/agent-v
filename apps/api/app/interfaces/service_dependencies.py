import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.app_config_service import AppConfigService
from app.application.services.status_service import StatusService
from app.infrastructure.external.health_checker.mysql_health_checker import (
    MySQLHealthChecker,
)
from app.infrastructure.external.health_checker.redis_health_checker import (
    RedisHealthChecker,
)
from app.infrastructure.repositories.file_app_config_repository import (
    FileAppConfigRepository,
)
from app.infrastructure.storage.mysql import get_db_session
from app.infrastructure.storage.redis import RedisClient, get_redis_client
from core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_app_config_service() -> AppConfigService:
    """获取应用配置服务实例.

    使用 lru_cache 实现单例模式，确保服务实例全局唯一.

    Returns:
        AppConfigService 单例实例.
    """
    logger.info("初始化 AppConfigService")
    settings = get_settings()
    repository = FileAppConfigRepository(settings.app_config_filepath)
    return AppConfigService(app_config_repository=repository)


@lru_cache
def get_health_checker_service(
        db_session: Annotated[AsyncSession, Depends(get_db_session)],
        redis_client: Annotated[RedisClient, Depends(get_redis_client)]
) -> StatusService:
    """获取状态服务"""
    logger.info("初始化 StatusService")
    postgres_checker = MySQLHealthChecker(db_session)
    redis_checker = RedisHealthChecker(redis_client)

    return StatusService(checkers=[postgres_checker, redis_checker])
