import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.logging import setup_logging
from app.interfaces.endpoints.routes import router
from core.config import get_settings

settings = get_settings()

setup_logging()
logger = logging.getLogger()

openapi_tags = [
    {
        "name": "状态模块",
        "description": "包含 **状态监测** 等API 接口，用于监测系统的运行状态。",
    }
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("wychmod agent正在启动")
        yield
    finally:
        logger.info("wychmod agent正在关闭")


app = FastAPI(
    title="wychmod通用智能体",
    description="wychmod是一个通用的AI Agent系统，可以完全私有部署，使用A2A+MCP连接Agent/Tool，同时支持在沙箱中运行各种内置工具和操作",
    lifespan=lifespan,
    openapi_tags=openapi_tags,
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# noqa: F821
app.include_router(router, prefix="/api")
