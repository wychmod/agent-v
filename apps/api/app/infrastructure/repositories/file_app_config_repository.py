from pathlib import Path

from app.domain.models.app_config import AppConfig
from app.domain.repositories.app_config_repository import AppConfigRepository


class FileAppConfigRepository(AppConfigRepository):
    def __init__(self, config_path: str) -> None:
        """构造函数，完成文件配置仓库的相关信息初始化"""
        # 1.获取当前根目录
        root_dir = Path.cwd()
        self._config_path = root_dir.joinpath(config_path)
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_file = self._config_path.with_suffix(".lock")  # 文件锁，替换文件后缀

    def load(self) -> AppConfig | None:
        """加载应用配置.

        Returns:
            配置对象，若不存在则返回None.
        """
        pass

    def save(self, app_config: AppConfig) -> None:
        """保存应用配置.

        Args:
            app_config: 要保存的配置对象.
        """
        pass
