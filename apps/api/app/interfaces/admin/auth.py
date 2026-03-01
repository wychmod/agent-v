"""管理后台认证提供者"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminUser, AuthProvider
from starlette_admin.exceptions import LoginFailed

from app.application.security.password_handler import PasswordHandler
from app.infrastructure.models.user_models import UserModel, UserRoleModel
from app.infrastructure.storage.mysql import get_mysql_client

logger = logging.getLogger(__name__)

ADMIN_ROLES = {"admin", "super_admin"}


class AdminAuthProvider(AuthProvider):
    """基于现有用户表的管理后台认证提供者，仅允许 admin/super_admin 角色访问。"""

    def __init__(self) -> None:
        super().__init__()
        self._password_handler = PasswordHandler()

    async def _get_admin_user(self, user_id: str) -> UserModel | None:
        """查询用户并预加载角色，验证管理员权限。"""
        session_maker = get_mysql_client().session
        async with session_maker() as session:
            stmt = (
                select(UserModel)
                .where(UserModel.id == user_id, UserModel.is_active.is_(True))
                .options(selectinload(UserModel.roles).selectinload(UserRoleModel.role))
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user is None:
                return None
            role_names = {ur.role.name for ur in user.roles}
            if not role_names & ADMIN_ROLES:
                return None
            return user

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        """处理管理后台登录。"""
        session_maker = get_mysql_client().session
        async with session_maker() as session:
            stmt = (
                select(UserModel)
                .where(
                    UserModel.username == username,
                    UserModel.is_active.is_(True),
                )
                .options(selectinload(UserModel.roles).selectinload(UserRoleModel.role))
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user is None or not self._password_handler.verify_password(
                password, user.password_hash
            ):
                raise LoginFailed("用户名或密码错误")

            role_names = {ur.role.name for ur in user.roles}
            if not role_names & ADMIN_ROLES:
                raise LoginFailed("无管理后台访问权限")

            request.session["user_id"] = user.id
            request.session["username"] = user.username
            logger.info(
                "管理员登录成功: user_id=%s, username=%s", user.id, user.username
            )
            return response

    async def is_authenticated(self, request: Request) -> bool:
        """验证当前请求是否已认证且拥有管理员角色。"""
        user_id = request.session.get("user_id")
        if not user_id:
            return False
        user = await self._get_admin_user(user_id)
        return user is not None

    def get_admin_user(self, request: Request) -> AdminUser | None:
        """获取当前管理员用户信息，用于界面右上角显示。

        注意：此方法为同步方法，因为 starlette-admin 的 AuthProvider
        基类中定义的是同步方法。我们需要从 session 中直接获取已保存的用户信息。
        """
        user_id = request.session.get("user_id")
        if not user_id:
            return None
        # 从 session 中获取保存的用户名（在 login 时设置）
        username = request.session.get("username")
        if not username:
            return None
        return AdminUser(username=username)

    async def logout(self, request: Request, response: Response) -> Response:
        """处理管理后台登出。"""
        user_id = request.session.get("user_id")
        request.session.clear()
        logger.info("管理员登出: user_id=%s", user_id)
        return response
