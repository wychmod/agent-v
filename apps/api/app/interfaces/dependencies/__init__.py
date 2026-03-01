"""认证依赖注入模块"""

from app.interfaces.dependencies.auth_dependencies import (
    get_auth_service,
    get_current_active_user,
    get_current_user,
    get_user_service,
    require_permission,
    require_roles,
)

__all__ = [
    "get_auth_service",
    "get_current_active_user",
    "get_current_user",
    "get_user_service",
    "require_permission",
    "require_roles",
]
