import logging

from app.domain.models.app_config import AppConfig, LLMConfig
from app.domain.repositories.app_config_repository import AppConfigRepository

logger = logging.getLogger(__name__)


class AppConfigService:
    """应用配置服务类."""

    def __init__(self, app_config_repository: AppConfigRepository) -> None:
        """初始化应用配置服务.

        Args:
            app_config_repository: 应用配置仓库实例.
        """
        self.app_config_repository = app_config_repository

    async def _load_app_config(self) -> AppConfig:
        """加载应用配置."""
        app_config = self.app_config_repository.load()
        if app_config is None:
            app_config = AppConfig(llm_config=LLMConfig())
            self.app_config_repository.save(app_config)
        return app_config

    async def get_llm_config(self) -> LLMConfig:
        """获取LLM配置."""
        app_config = await self._load_app_config()
        return app_config.llm_config

    async def update_llm_config(self, llm_config: LLMConfig) -> LLMConfig:
        """更新LLM配置.

        Args:
            llm_config: 新的LLM配置对象.

        Returns:
            更新后的LLM配置.
        """
        app_config = await self._load_app_config()
        if not llm_config.api_key.strip():
            llm_config.api_key = app_config.llm_config.api_key
        app_config.llm_config = llm_config
        self.app_config_repository.save(app_config)

        return app_config.llm_config
