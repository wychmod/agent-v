"""角色仓储协议"""

from typing import Protocol

from app.domain.models.user import Permission, Role


class RoleRepository(Protocol):
    """角色仓储协议，定义角色数据持久化的接口契约"""

    async def create(self, role: Role) -> Role:
        """创建新角色"""
        ...

    async def get_by_id(self, role_id: int) -> Role | None:
        """根据ID获取角色"""
        ...

    async def get_by_name(self, name: str) -> Role | None:
        """根据名称获取角色"""
        ...

    async def list_all(self) -> list[Role]:
        """获取所有角色"""
        ...

    async def get_user_roles(self, user_id: str) -> list[Role]:
        """获取用户的所有角色"""
        ...

    async def assign_role_to_user(
        self, user_id: str, role_id: int, assigned_by: str | None = None
    ) -> None:
        """为用户分配角色"""
        ...

    async def remove_role_from_user(self, user_id: str, role_id: int) -> None:
        """移除用户的角色"""
        ...

    async def user_has_role(self, user_id: str, role_name: str) -> bool:
        """检查用户是否拥有指定角色"""
        ...

    async def update(self, role: Role) -> Role:
        """更新角色信息"""
        ...

    async def delete(self, role_id: int) -> bool:
        """删除角色"""
        ...

    async def exists_by_name(self, name: str) -> bool:
        """检查角色名是否已存在"""
        ...

    async def count_users_with_role(self, role_id: int) -> int:
        """统计拥有该角色的用户数"""
        ...


class PermissionRepository(Protocol):
    """权限仓储协议，定义权限数据持久化的接口契约"""

    async def create(self, permission: Permission) -> Permission:
        """创建新权限"""
        ...

    async def get_by_id(self, permission_id: int) -> Permission | None:
        """根据ID获取权限"""
        ...

    async def get_by_resource_action(
        self, resource: str, action: str
    ) -> Permission | None:
        """根据资源和操作获取权限"""
        ...

    async def list_all(self) -> list[Permission]:
        """获取所有权限"""
        ...

    async def get_role_permissions(self, role_id: int) -> list[Permission]:
        """获取角色的所有权限"""
        ...

    async def get_user_permissions(self, user_id: str) -> list[Permission]:
        """获取用户的所有权限（通过角色）"""
        ...

    async def assign_permission_to_role(self, role_id: int, permission_id: int) -> None:
        """为角色分配权限"""
        ...

    async def remove_permission_from_role(
        self, role_id: int, permission_id: int
    ) -> None:
        """移除角色的权限"""
        ...

    async def check_user_permission(
        self, user_id: str, resource: str, action: str
    ) -> bool:
        """检查用户是否拥有指定权限"""
        ...

    async def update(self, permission: Permission) -> Permission | None:
        """更新权限信息"""
        ...

    async def delete(self, permission_id: int) -> bool:
        """删除权限"""
        ...
