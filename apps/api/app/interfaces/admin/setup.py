"""管理后台初始化"""

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
    """初始化并挂载 starlette-admin 到 FastAPI 应用。

    必须在 MySQL 初始化完成后调用（lifespan 中）。
    """
    mysql_client = get_mysql_client()

    admin = Admin(
        engine=mysql_client.engine,
        title="Agent 管理后台",
        base_url="/admin",
        auth_provider=AdminAuthProvider(),
    )

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

    admin.mount_to(app)
    logger.info("管理后台已挂载到 /admin")
    return admin
