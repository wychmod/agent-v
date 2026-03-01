"""API路由聚合模块

该模块负责整合所有子模块的路由，提供统一的API路由入口。
"""

from fastapi import APIRouter

from . import (
    app_config_routes,
    auth_routes,
    permission_routes,
    role_routes,
    status_routes,
    user_routes,
)


def create_api_routes() -> APIRouter:
    """创建并配置API路由

    将所有子模块的路由注册到主路由器中，实现路由的集中管理。

    Returns:
        APIRouter: 配置完成的API路由器实例
    """
    api_router = APIRouter()
    # 注册状态检查相关路由
    api_router.include_router(status_routes.router)
    api_router.include_router(app_config_routes.router)
    # 注册认证和用户管理路由
    api_router.include_router(auth_routes.router)
    api_router.include_router(user_routes.router)
    api_router.include_router(user_routes.roles_router)
    # 注册角色和权限管理路由
    api_router.include_router(role_routes.router)
    api_router.include_router(permission_routes.router)
    return api_router


# 创建全局路由器实例供应用使用
router = create_api_routes()
