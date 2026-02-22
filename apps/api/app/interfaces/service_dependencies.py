import logging
from functools import lru_cache

from app.application.services.app_config_service import AppConfigService
from app.infrastructure.repositories.file_app_config_repository import (
    FileAppConfigRepository,
)
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
