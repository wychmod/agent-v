"""应用程序主入口

配置FastAPI应用的核心功能，包括路由、中间件、日志等。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.logging import setup_logging
from app.infrastructure.storage.redis import get_redis_client
from app.interfaces.endpoints.routes import router
from app.interfaces.errors.exception_handles import register_exception_handlers
from core.config import get_settings

# 加载应用配置
settings = get_settings()

# 初始化日志系统
setup_logging()
logger = logging.getLogger()

# OpenAPI文档标签配置
openapi_tags = [
    {
        "name": "状态模块",
        "description": "包含 **状态监测** 等API 接口，用于监测系统的运行状态。",
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理

    管理FastAPI应用的启动和关闭过程，处理资源初始化和清理。

    Args:
        app (FastAPI): FastAPI应用实例

    Yields:
        None: 应用运行期间

    Note:
        - 启动阶段：记录启动日志，可扩展为初始化数据库、缓存等资源
        - 关闭阶段：记录关闭日志，可扩展为释放连接池、关闭文件句柄等
    """
    try:
        logger.info("wychmod agent正在启动")
        await get_redis_client().init()
        yield
    finally:

        await get_redis_client().shutdown()
        logger.info("wychmod agent正在关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title="wychmod通用智能体",
    description="wychmod是一个通用的AI Agent系统，可以完全私有部署，使用A2A+MCP连接Agent/Tool，同时支持在沙箱中运行各种内置工具和操作",
    lifespan=lifespan,
    openapi_tags=openapi_tags,
    version="1.0.0",
)


# 配置CORS中间件，允许跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应指定具体域名
    allow_credentials=True,  # 允许携带凭证（cookies、authorization headers等）
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# 注册异常处理
register_exception_handlers(app)

# 注册应用路由，所有API端点均在/api前缀下
app.include_router(router, prefix="/api")
