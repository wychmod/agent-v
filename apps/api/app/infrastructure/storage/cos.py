import logging
from functools import lru_cache

from qcloud_cos import CosConfig, CosS3Client  # type: ignore

from core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class Cos:
    """腾讯云Cos对象存储"""

    def __init__(self) -> None:
        """构造函数，完成配置获取+Cos客户端初始化赋值"""
        self._settings: Settings = get_settings()
        self._client: CosS3Client | None = None

    async def init(self) -> None:
        """初始化Cos客户端"""
        if self._client is not None:
            logger.warning("Cos 已经初始化，跳过重复初始化")
            return

        try:
            logger.info("初始化 Cos 配置")
            config = CosConfig(
                SecretId=self._settings.cos_secret_id,
                SecretKey=self._settings.cos_secret_key,
                Region=self._settings.cos_region,
                Token=None,
                Scheme=self._settings.cos_scheme,
            )
            self._client = CosS3Client(config)
            logger.info("Cos 配置初始化成功")
        except Exception as e:
            logger.error("Cos 配置初始化失败: %s", e)
            raise ConnectionError(f"无法连接到 Cos: {e}") from e

    async def shutdown(self) -> None:
        """关闭Cos客户端"""
        if self._client is not None:
            self._client = None
            logger.info("Cos 配置已关闭")
        get_cos.cache_clear()

    @property
    def client(self) -> CosS3Client:
        """获取已初始化的Cos客户端实例"""
        if self._client is None:
            raise RuntimeError("Cos 未初始化，请先调用 init()")
        return self._client


@lru_cache
def get_cos() -> Cos:
    """使用lru_cache实现单例模式，获取腾讯云cos对象存储"""
    return Cos()
