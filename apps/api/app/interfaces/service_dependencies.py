"""服务层依赖注入模块

本模块提供非认证相关的服务依赖项。

主要功能:
- 应用配置服务依赖注入
- 系统健康检查服务依赖注入

依赖项说明:
- get_app_config_service: 应用配置服务（单例）
- get_health_checker_service: 系统状态检查服务（单例）

Note:
    使用 lru_cache 装饰器实现单例模式，
    确保服务实例在应用生命周期内唯一。
"""

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
    """获取应用配置服务单例实例

    流程:
    1. 获取应用全局配置
    2. 创建文件配置仓储
    3. 初始化配置服务

    Returns:
        AppConfigService: 应用配置服务单例实例
    """
    logger.info("初始化 AppConfigService")
    settings = get_settings()
    repository = FileAppConfigRepository(settings.app_config_filepath)
    return AppConfigService(app_config_repository=repository)


@lru_cache
def get_health_checker_service(
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    redis_client: Annotated[RedisClient, Depends(get_redis_client)],
) -> StatusService:
    """获取系统状态检查服务单例实例

    组装各组件的健康检查器，用于系统状态监控。

    Args:
        db_session: 数据库会话
        redis_client: Redis 客户端

    Returns:
        StatusService: 包含 MySQL 和 Redis 健康检查的状态服务
    """
    logger.info("初始化 StatusService")
    # 创建各组件的健康检查器
    postgres_checker = MySQLHealthChecker(db_session)
    redis_checker = RedisHealthChecker(redis_client)

    return StatusService(checkers=[postgres_checker, redis_checker])
