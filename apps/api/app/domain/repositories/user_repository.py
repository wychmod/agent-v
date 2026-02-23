"""用户仓储协议"""

from typing import Protocol

from app.domain.models.user import User, UserWithPassword


class UserRepository(Protocol):
    """用户仓储协议，定义用户数据持久化的接口契约"""

    async def create(self, user: UserWithPassword) -> User:
        """创建新用户"""
        ...

    async def get_by_id(self, user_id: str) -> User | None:
        """根据ID获取用户"""
        ...

    async def get_by_email(self, email: str) -> UserWithPassword | None:
        """根据邮箱获取用户（含密码哈希，用于登录验证）"""
        ...

    async def get_by_username(self, username: str) -> User | None:
        """根据用户名获取用户"""
        ...

    async def update(self, user: User) -> User:
        """更新用户信息"""
        ...

    async def update_password(self, user_id: str, password_hash: str) -> None:
        """更新用户密码"""
        ...

    async def update_last_login(self, user_id: str) -> None:
        """更新最后登录时间"""
        ...

    async def update_verified_status(self, user_id: str, is_verified: bool) -> None:
        """更新邮箱验证状态"""
        ...

    async def delete(self, user_id: str) -> bool:
        """软删除用户（设置 is_active=False）"""
        ...

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> list[User]:
        """分页查询用户列表"""
        ...

    async def count(self, is_active: bool | None = None) -> int:
        """统计用户数量"""
        ...

    async def exists_by_email(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        ...

    async def exists_by_username(self, username: str) -> bool:
        """检查用户名是否已存在"""
        ...
