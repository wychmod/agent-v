"""应用程序主入口模块

本模块是 FastAPI 应用的核心入口，负责配置和启动整个应用。

主要功能:
- 创建和配置 FastAPI 应用实例
- 管理应用生命周期（启动/关闭）
- 配置中间件（CORS、Session）
- 注册路由和异常处理器
- 初始化各类外部服务连接

应用架构:
- API 端点: /api/* 前缀下的所有业务接口
- 管理后台: /admin 路径下的后台管理界面
- 健康检查: /api/status 系统状态检查

启动流程:
1. 加载配置和初始化日志
2. 创建 FastAPI 应用实例
3. 配置 CORS 和 Session 中间件
4. 注册全局异常处理器
5. 挂载 API 路由
6. 在 lifespan 中初始化数据库、缓存等资源

生产部署:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.infrastructure.logging import setup_logging
from app.infrastructure.storage.cos import get_cos
from app.infrastructure.storage.mysql import get_mysql_client
from app.infrastructure.storage.redis import get_redis_client
from app.interfaces.admin.setup import setup_admin
from app.interfaces.endpoints.routes import router
from app.interfaces.errors.exception_handles import register_exception_handlers
from core.config import get_settings

# 加载应用配置
settings = get_settings()

# 初始化日志系统
setup_logging()
logger = logging.getLogger()

# OpenAPI 文档标签配置，用于 Swagger UI 文档分组
openapi_tags = [
    {
        "name": "状态模块",
        "description": "包含 **状态监测** 等API 接口，用于监测系统的运行状态。",
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理器

    管理 FastAPI 应用的启动和关闭过程，处理资源初始化和清理。
    使用 asynccontextmanager 实现优雅的资源管理。

    流程:
    启动阶段:
    1. 记录启动日志
    2. 初始化 Redis 连接
    3. 初始化 MySQL 连接
    4. 初始化 COS 对象存储
    5. 挂载管理后台

    关闭阶段:
    1. 关闭 COS 连接
    2. 关闭 MySQL 连接
    3. 关闭 Redis 连接
    4. 记录关闭日志

    Args:
        app: FastAPI 应用实例

    Yields:
        None: 应用运行期间持续 yield

    Note:
        资源初始化顺序和关闭顺序相反，确保依赖关系正确处理
    """
    try:
        logger.info("wychmod agent正在启动")
        # 按依赖顺序初始化外部服务
        await get_redis_client().init()
        await get_mysql_client().init()
        await get_cos().init()
        # 挂载管理后台（需要在 MySQL 初始化后）
        setup_admin(app)
        yield
    finally:
        # 按相反顺序关闭资源
        await get_cos().shutdown()
        await get_mysql_client().shutdown()
        await get_redis_client().shutdown()
        logger.info("wychmod agent正在关闭")


# 创建 FastAPI 应用实例
app = FastAPI(
    title="wychmod通用智能体",
    description="wychmod是一个通用的AI Agent系统，可以完全私有部署，使用A2A+MCP连接Agent/Tool，同时支持在沙箱中运行各种内置工具和操作",
    lifespan=lifespan,
    openapi_tags=openapi_tags,
    version="1.0.0",
)

# 配置 CORS 中间件，允许跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应指定具体域名
    allow_credentials=True,  # 允许携带凭证（cookies、authorization headers等）
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 HTTP 头
)

# 配置 Session 中间件，用于管理后台认证状态存储
app.add_middleware(SessionMiddleware, secret_key=settings.admin_secret_key)

# 注册全局异常处理器
register_exception_handlers(app)

# 注册应用路由，所有 API 端点均在 /api 前缀下
app.include_router(router, prefix="/api")
