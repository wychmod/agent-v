"""腾讯云对象存储（COS）客户端模块

本模块提供腾讯云 COS 对象存储服务的客户端封装。

主要功能:
- COS 客户端初始化与连接管理
- 单例模式确保全局唯一实例
- 异步生命周期管理

使用方式:
    cos = get_cos()
    await cos.init()
    client = cos.client
    # 使用 client 进行文件操作
    await cos.shutdown()

依赖配置:
- cos_secret_id: 腾讯云访问密钥 ID
- cos_secret_key: 腾讯云访问密钥
- cos_region: COS 存储桶所在地域
- cos_scheme: 请求协议（http/https）
"""

import logging
from functools import lru_cache

from qcloud_cos import CosConfig, CosS3Client  # type: ignore

from core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class Cos:
    """腾讯云 COS 对象存储客户端管理类

    负责 COS 客户端的初始化、关闭和访问管理。
    使用内部状态管理连接生命周期。

    Attributes:
        _settings: 应用配置实例
        _client: COS S3 客户端实例，未初始化时为 None
    """

    def __init__(self) -> None:
        """初始化 Cos 实例

        获取应用配置并准备客户端初始化。
        实际的客户端连接在调用 init() 时创建。
        """
        self._settings: Settings = get_settings()
        self._client: CosS3Client | None = None

    async def init(self) -> None:
        """初始化 COS 客户端连接

        流程:
        1. 检查是否已初始化，避免重复初始化
        2. 创建 COS 配置对象
        3. 初始化 COS S3 客户端

        Raises:
            ConnectionError: COS 配置初始化失败时抛出
        """
        if self._client is not None:
            logger.warning("Cos 已经初始化，跳过重复初始化")
            return

        try:
            logger.info("初始化 Cos 配置")
            # 创建 COS 配置对象
            config = CosConfig(
                SecretId=self._settings.cos_secret_id,
                SecretKey=self._settings.cos_secret_key,
                Region=self._settings.cos_region,
                Token=None,  # 临时密钥 Token，使用永久密钥时为 None
                Scheme=self._settings.cos_scheme,
            )
            self._client = CosS3Client(config)
            logger.info("Cos 配置初始化成功")
        except Exception as e:
            logger.error("Cos 配置初始化失败: %s", e)
            raise ConnectionError(f"无法连接到 Cos: {e}") from e

    async def shutdown(self) -> None:
        """关闭 COS 客户端连接

        清理客户端资源并清除单例缓存。
        """
        if self._client is not None:
            self._client = None
            logger.info("Cos 配置已关闭")
        # 清除单例缓存，下次获取时将创建新实例
        get_cos.cache_clear()

    @property
    def client(self) -> CosS3Client:
        """获取已初始化的 COS 客户端实例

        Returns:
            CosS3Client: 腾讯云 COS S3 兼容客户端

        Raises:
            RuntimeError: 如果客户端未初始化
        """
        if self._client is None:
            raise RuntimeError("Cos 未初始化，请先调用 init()")
        return self._client


@lru_cache
def get_cos() -> Cos:
    """获取 Cos 单例实例

    使用 lru_cache 装饰器实现单例模式，
    确保全局只有一个 Cos 客户端实例。

    Returns:
        Cos: COS 客户端管理实例
    """
    return Cos()
