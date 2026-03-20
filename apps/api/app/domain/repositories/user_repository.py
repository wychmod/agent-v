"""用户仓储协议模块

本模块定义用户数据持久化的接口协议。

支持用户的基本CRUD操作、身份验证相关查询、
以及分页列表等功能。
"""

from typing import Protocol

from app.domain.models.user import User, UserWithPassword


class UserRepository(Protocol):
    """用户仓储协议

    定义用户数据持久化的接口契约。
    实现类需要提供完整的用户数据管理功能。
    """

    async def create(self, user: UserWithPassword) -> User:
        """创建新用户

        Args:
            user: 带密码哈希的用户对象

        Returns:
            创建后的用户对象（不含密码）
        """
        ...

    async def get_by_id(self, user_id: str) -> User | None:
        """根据ID获取用户

        Args:
            user_id: 用户ID

        Returns:
            用户对象，不存在返回None
        """
        ...

    async def get_by_email(self, email: str) -> UserWithPassword | None:
        """根据邮箱获取用户（含密码哈希，用于登录验证）

        Args:
            email: 用户邮箱

        Returns:
            带密码的用户对象，不存在返回None
        """
        ...

    async def get_by_username(self, username: str) -> User | None:
        """根据用户名获取用户

        Args:
            username: 用户名

        Returns:
            用户对象，不存在返回None
        """
        ...

    async def update(self, user: User) -> User:
        """更新用户信息

        Args:
            user: 用户对象

        Returns:
            更新后的用户对象
        """
        ...

    async def update_password(self, user_id: str, password_hash: str) -> None:
        """更新用户密码

        Args:
            user_id: 用户ID
            password_hash: 新密码哈希
        """
        ...

    async def update_last_login(self, user_id: str) -> None:
        """更新最后登录时间

        Args:
            user_id: 用户ID
        """
        ...

    async def update_verified_status(self, user_id: str, is_verified: bool) -> None:
        """更新邮箱验证状态

        Args:
            user_id: 用户ID
            is_verified: 验证状态
        """
        ...

    async def delete(self, user_id: str) -> bool:
        """软删除用户（设置 is_active=False）

        Args:
            user_id: 用户ID

        Returns:
            删除是否成功
        """
        ...

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> list[User]:
        """分页查询用户列表

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            is_active: 激活状态过滤

        Returns:
            用户列表
        """
        ...

    async def count(self, is_active: bool | None = None) -> int:
        """统计用户数量

        Args:
            is_active: 激活状态过滤

        Returns:
            用户总数
        """
        ...

    async def exists_by_email(self, email: str) -> bool:
        """检查邮箱是否已存在

        Args:
            email: 邮箱地址

        Returns:
            是否存在
        """
        ...

    async def exists_by_username(self, username: str) -> bool:
        """检查用户名是否已存在

        Args:
            username: 用户名

        Returns:
            是否存在
        """
        ...
