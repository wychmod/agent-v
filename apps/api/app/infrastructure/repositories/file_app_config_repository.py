import logging
from pathlib import Path

import yaml
from filelock import FileLock

from app.application.errors.exceptions import ServerRequestsError
from app.domain.models.app_config import AppConfig, LLMConfig
from app.domain.repositories.app_config_repository import AppConfigRepository

logger = logging.getLogger(__name__)


class FileAppConfigRepository(AppConfigRepository):
    def __init__(self, config_path: str) -> None:
        """初始化文件配置仓库."""
        root_dir = Path.cwd()
        self._config_path = root_dir.joinpath(config_path)
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_file = self._config_path.with_suffix(".lock")

    def _create_default_app_config_if_not_exists(self) -> None:
        """配置文件不存在时创建默认配置."""
        if not self._config_path.exists():
            default_config = AppConfig(llm_config=LLMConfig())
            self.save(default_config)

    def load(self) -> AppConfig | None:
        """加载应用配置."""
        self._create_default_app_config_if_not_exists()
        try:
            with open(self._config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return AppConfig.model_validate(data) if data else None
        except Exception as e:
            logger.error(f"读取应用配置失败: {str(e)}")
            raise ServerRequestsError("读取应用配置失败，请稍后尝试") from None

    def save(self, app_config: AppConfig) -> None:
        """保存应用配置."""
        lock = FileLock(self._lock_file, timeout=5)
        try:
            with lock:
                data_to_dump = app_config.model_dump(mode="json")
                with open(self._config_path, "w", encoding="utf-8") as f:
                    yaml.dump(data_to_dump, f, allow_unicode=True, sort_keys=False)
        except TimeoutError:
            logger.error("无法获取配置文件")
            raise ServerRequestsError("写入配置文件失败，请稍后尝试") from None
