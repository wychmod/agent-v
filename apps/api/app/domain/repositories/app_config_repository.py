from typing import Optional, Protocol

from app.domain.models.app_config import AppConfig


class AppConfigRepository(Protocol):
    """应用配置仓库协议，定义配置持久化的接口契约.

    实现该协议的具体仓库类可用于从不同存储后端（文件、数据库、Redis等）
    加载和保存应用配置。
    """

    def load(self) -> Optional[AppConfig]:
        """加载应用配置.

        Returns:
            配置对象，若不存在则返回None.
        """
        ...

    def save(self, app_config: AppConfig) -> None:
        """保存应用配置.

        Args:
            app_config: 要保存的配置对象.
        """
        ...