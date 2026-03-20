"""应用配置服务模块

本模块提供应用配置的管理功能，包括加载、获取和更新配置。

主要功能:
- 加载应用配置（从文件或默认值）
- 获取LLM（大语言模型）配置
- 更新LLM配置

配置存储:
配置通过仓储层持久化，支持文件存储等多种方式。
"""

import logging

from app.domain.models.app_config import AppConfig, LLMConfig
from app.domain.repositories.app_config_repository import AppConfigRepository

logger = logging.getLogger(__name__)


class AppConfigService:
    """应用配置服务

    负责应用配置的加载、获取和更新操作。
    配置采用懒加载策略，首次访问时自动初始化。

    Attributes:
        app_config_repository: 应用配置仓储实例
    """

    def __init__(self, app_config_repository: AppConfigRepository) -> None:
        """初始化应用配置服务

        Args:
            app_config_repository: 应用配置仓储实例
        """
        self.app_config_repository = app_config_repository

    async def _load_app_config(self) -> AppConfig:
        """加载应用配置

        流程:
        1. 尝试从仓储加载配置
        2. 如果配置不存在，创建默认配置并保存
        3. 返回配置对象

        Returns:
            应用配置对象
        """
        app_config = self.app_config_repository.load()
        if app_config is None:
            # 配置不存在时创建默认配置
            app_config = AppConfig(llm_config=LLMConfig())
            self.app_config_repository.save(app_config)
        return app_config

    async def get_llm_config(self) -> LLMConfig:
        """获取LLM配置

        Returns:
            LLM配置对象，包含模型名称、API密钥等信息
        """
        app_config = await self._load_app_config()
        return app_config.llm_config

    async def update_llm_config(self, llm_config: LLMConfig) -> LLMConfig:
        """更新LLM配置

        流程:
        1. 加载当前配置
        2. 如果新配置中API密钥为空，保留原有密钥
        3. 保存更新后的配置

        Args:
            llm_config: 新的LLM配置对象

        Returns:
            更新后的LLM配置
        """
        app_config = await self._load_app_config()
        # 如果新配置未提供API密钥，保留原有密钥（避免意外清空）
        if not llm_config.api_key.strip():
            llm_config.api_key = app_config.llm_config.api_key
        app_config.llm_config = llm_config
        self.app_config_repository.save(app_config)

        return app_config.llm_config
