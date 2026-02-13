"""MySQL client module.

提供异步 MySQL 数据库连接的初始化、会话管理和关闭功能。
使用单例模式通过 get_mysql 函数获取客户端实例。
支持异步上下文管理器进行资源管理。
"""

import logging
from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Self

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import Settings, get_settings

logger: logging.Logger = logging.getLogger(__name__)


class MySQLClient:
    """MySQL 异步客户端管理类。

    负责 MySQL 数据库连接的初始化、关闭和会话管理。
    使用 SQLAlchemy 异步引擎和会话工厂管理数据库连接生命周期。

    Attributes:
        _engine: SQLAlchemy 异步引擎实例，未初始化时为 None
        _session: 异步会话工厂，未初始化时为 None
        _settings: 应用配置实例
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """初始化 MySQLClient 实例。

        Args:
            settings: 配置实例，为 None 时自动获取全局配置
        """
        self._engine: AsyncEngine | None = None
        self._session: async_sessionmaker[AsyncSession] | None = None
        self._settings: Settings = settings if settings is not None else get_settings()

    async def init(self) -> None:
        """初始化 MySQL 数据库连接。

        创建异步数据库引擎和会话工厂，验证连接可用性。
        如果已初始化则记录警告并返回。

        Raises:
            ConnectionError: MySQL 连接失败时抛出
        """
        if self._engine is not None:
            logger.warning("MySQL client 已经初始化，跳过重复初始化")
            return

        try:
            logger.info("初始化 MySQL 连接")
            self._engine = create_async_engine(
                self._settings.sqlalchemy_database_uri,
                echo=True if self._settings.env == "development" else False,
            )
            self._session = async_sessionmaker(
                self._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )

            # 验证连接可用性
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            logger.info("MySQL client 初始化成功")
        except Exception as e:
            logger.error("MySQL 初始化失败: %s", e)
            raise ConnectionError(f"无法连接到 MySQL: {e}") from e

    async def shutdown(self) -> None:
        """关闭 MySQL 数据库连接。

        安全关闭数据库引擎并清理相关资源。
        同时清除 get_mysql_client 的缓存以确保下次获取新实例。
        """
        if self._engine is not None:
            try:
                await self._engine.dispose()
                logger.info("MySQL client 连接已关闭")
            except Exception as e:
                logger.warning("关闭 MySQL 连接时发生错误: %s", e)
            finally:
                self._engine = None
                self._session = None

        get_mysql_client.cache_clear()
        logger.debug("MySQL client 缓存已清除")

    @property
    def session(self) -> async_sessionmaker[AsyncSession]:
        """获取已初始化的数据库会话工厂。

        Returns:
            async_sessionmaker: 异步会话工厂

        Raises:
            RuntimeError: 如果 MySQL client 未初始化
        """
        if self._session is None:
            raise RuntimeError("MySQL client 未初始化，请先调用 init()")
        return self._session

    @property
    def engine(self) -> AsyncEngine:
        """获取已初始化的数据库引擎实例。

        Returns:
            AsyncEngine: SQLAlchemy 异步引擎

        Raises:
            RuntimeError: 如果 MySQL client 未初始化
        """
        if self._engine is None:
            raise RuntimeError("MySQL client 未初始化，请先调用 init()")
        return self._engine

    async def __aenter__(self) -> Self:
        """异步上下文管理器入口。

        Returns:
            MySQLClient: 当前实例
        """
        await self.init()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """异步上下文管理器出口。

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪
        """
        await self.shutdown()


@lru_cache(maxsize=1)
def get_mysql_client(settings: Settings | None = None) -> MySQLClient:
    """获取 MySQLClient 单例实例。

    使用 lru_cache 确保全局只有一个 MySQLClient 实例。

    Args:
        settings: 可选的配置实例，用于依赖注入

    Returns:
        MySQLClient: MySQL 客户端管理实例
    """
    return MySQLClient(settings=settings)


# 向后兼容的别名
get_mysql = get_mysql_client
MySQL = MySQLClient


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖项，用于在每个请求中获取数据库会话。

    通过异步生成器管理会话生命周期，确保会话正确提交或回滚。

    Yields:
        AsyncSession: 数据库会话实例

    Raises:
        Exception: 数据库操作异常时回滚并抛出
    """
    db = get_mysql_client()
    session_factory = db.session
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
