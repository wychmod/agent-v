"""管理后台初始化模块

本模块负责初始化和配置 starlette-admin 管理后台。

主要功能:
- 创建 Admin 实例并配置数据库引擎
- 注册所有模型视图
- 挂载管理后台到 FastAPI 应用

管理视图:
- 用户管理 (UserView)
- 角色管理 (RoleView)
- 权限管理 (PermissionView)
- 用户-角色关联 (UserRoleView)
- 角色-权限关联 (RolePermissionView)
- 审计日志 (AuditLogView)

访问路径: /admin

Note:
    必须在 MySQL 初始化完成后调用 setup_admin 函数
"""

import logging

from fastapi import FastAPI
from starlette_admin.contrib.sqla import Admin

from app.infrastructure.models.user_models import (
    AuditLogModel,
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserModel,
    UserRoleModel,
)
from app.infrastructure.storage.mysql import get_mysql_client

from .auth import AdminAuthProvider
from .views import (
    AuditLogView,
    PermissionView,
    RolePermissionView,
    RoleView,
    UserRoleView,
    UserView,
)

logger = logging.getLogger(__name__)


def setup_admin(app: FastAPI) -> Admin:
    """初始化并挂载 starlette-admin 到 FastAPI 应用

    流程:
    1. 获取 MySQL 客户端实例
    2. 创建 Admin 实例，配置数据库引擎和认证
    3. 注册所有模型视图
    4. 挂载到 FastAPI 应用

    Args:
        app: FastAPI 应用实例

    Returns:
        Admin: 配置完成的管理后台实例

    Note:
        必须在 MySQL 初始化完成后调用（lifespan 中）
    """
    mysql_client = get_mysql_client()

    # 创建 Admin 实例
    admin = Admin(
        engine=mysql_client.engine,
        title="Agent 管理后台",
        base_url="/admin",
        auth_provider=AdminAuthProvider(),
    )

    # 注册模型视图
    admin.add_view(UserView(UserModel, label="用户管理", icon="fa fa-users"))
    admin.add_view(RoleView(RoleModel, label="角色管理", icon="fa fa-shield-halved"))
    admin.add_view(PermissionView(PermissionModel, label="权限管理", icon="fa fa-key"))
    admin.add_view(
        UserRoleView(UserRoleModel, label="用户-角色关联", icon="fa fa-user-tag")
    )
    admin.add_view(
        RolePermissionView(
            RolePermissionModel, label="角色-权限关联", icon="fa fa-lock"
        )
    )
    admin.add_view(
        AuditLogView(AuditLogModel, label="审计日志", icon="fa fa-clipboard-list")
    )

    # 挂载到 FastAPI 应用
    admin.mount_to(app)
    logger.info("管理后台已挂载到 /admin")
    return admin
