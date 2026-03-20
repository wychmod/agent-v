"""管理后台认证提供者模块

本模块提供基于现有用户表的管理后台认证功能。

主要功能:
- 管理员登录认证
- 会话状态验证
- 管理员信息获取
- 登出处理

访问控制:
- 仅允许 admin 和 super_admin 角色访问管理后台
- 用户必须处于激活状态才能登录
- 使用 Session 存储登录状态

安全特性:
- 密码使用 bcrypt 加密验证
- 登录失败记录日志
- 登出时清除所有 Session 数据
"""

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

# 允许访问管理后台的角色集合
ADMIN_ROLES = {"admin", "super_admin"}


class AdminAuthProvider(AuthProvider):
    """基于现有用户表的管理后台认证提供者

    实现 starlette-admin 的 AuthProvider 接口，
    仅允许拥有 admin 或 super_admin 角色的用户访问。

    Attributes:
        _password_handler: 密码处理器，用于验证登录密码
    """

    def __init__(self) -> None:
        """初始化认证提供者"""
        super().__init__()
        self._password_handler = PasswordHandler()

    async def _get_admin_user(self, user_id: str) -> UserModel | None:
        """查询用户并验证管理员权限

        流程:
        1. 查询用户信息并预加载角色
        2. 验证用户是否激活
        3. 检查是否拥有管理员角色

        Args:
            user_id: 用户唯一标识

        Returns:
            UserModel | None: 有管理员权限返回用户对象，否则返回 None
        """
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
            # 检查用户角色是否包含管理员角色
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
        """处理管理后台登录

        流程:
        1. 根据用户名查询用户
        2. 验证密码
        3. 检查管理员权限
        4. 设置 Session 信息

        Args:
            username: 用户名
            password: 密码
            remember_me: 是否记住登录（当前未使用）
            request: 请求对象
            response: 响应对象

        Returns:
            Response: 登录成功后的响应

        Raises:
            LoginFailed: 用户名/密码错误或无管理权限
        """
        session_maker = get_mysql_client().session
        async with session_maker() as session:
            # 查询用户并预加载角色
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

            # 验证用户存在且密码正确
            if user is None or not self._password_handler.verify_password(
                password, user.password_hash
            ):
                raise LoginFailed("用户名或密码错误")

            # 检查管理员权限
            role_names = {ur.role.name for ur in user.roles}
            if not role_names & ADMIN_ROLES:
                raise LoginFailed("无管理后台访问权限")

            # 设置 Session
            request.session["user_id"] = user.id
            request.session["username"] = user.username
            logger.info(
                "管理员登录成功: user_id=%s, username=%s", user.id, user.username
            )
            return response

    async def is_authenticated(self, request: Request) -> bool:
        """验证当前请求是否已认证且拥有管理员角色

        Args:
            request: 请求对象

        Returns:
            bool: 已认证且有管理员权限返回 True
        """
        user_id = request.session.get("user_id")
        if not user_id:
            return False
        user = await self._get_admin_user(user_id)
        return user is not None

    def get_admin_user(self, request: Request) -> AdminUser | None:
        """获取当前管理员用户信息

        用于界面右上角显示当前登录用户名。

        Note:
            此方法为同步方法，因为 starlette-admin 的 AuthProvider
            基类中定义的是同步方法。从 session 中直接获取已保存的用户信息。

        Args:
            request: 请求对象

        Returns:
            AdminUser | None: 管理员用户信息，未登录返回 None
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
        """处理管理后台登出

        清除 Session 中的所有数据。

        Args:
            request: 请求对象
            response: 响应对象

        Returns:
            Response: 登出后的响应
        """
        user_id = request.session.get("user_id")
        request.session.clear()
        logger.info("管理员登出: user_id=%s", user_id)
        return response
