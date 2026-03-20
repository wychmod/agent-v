"""角色和权限仓储协议模块

本模块定义角色和权限数据持久化的接口协议。

包含两个协议:
- RoleRepository: 角色仓储协议
- PermissionRepository: 权限仓储协议

遵循RBAC（基于角色的访问控制）模型设计。
"""

from typing import Protocol

from app.domain.models.user import Permission, Role


class RoleRepository(Protocol):
    """角色仓储协议

    定义角色数据持久化的接口契约。
    支持角色的CRUD操作和用户角色关联管理。
    """

    async def create(self, role: Role) -> Role:
        """创建新角色

        Args:
            role: 角色对象

        Returns:
            创建后的角色（含ID）
        """
        ...

    async def get_by_id(self, role_id: int) -> Role | None:
        """根据ID获取角色

        Args:
            role_id: 角色ID

        Returns:
            角色对象，不存在返回None
        """
        ...

    async def get_by_name(self, name: str) -> Role | None:
        """根据名称获取角色

        Args:
            name: 角色名称

        Returns:
            角色对象，不存在返回None
        """
        ...

    async def list_all(self) -> list[Role]:
        """获取所有角色

        Returns:
            角色列表
        """
        ...

    async def get_user_roles(self, user_id: str) -> list[Role]:
        """获取用户的所有角色

        Args:
            user_id: 用户ID

        Returns:
            角色列表
        """
        ...

    async def assign_role_to_user(
        self, user_id: str, role_id: int, assigned_by: str | None = None
    ) -> None:
        """为用户分配角色

        Args:
            user_id: 用户ID
            role_id: 角色ID
            assigned_by: 分配操作者ID
        """
        ...

    async def remove_role_from_user(self, user_id: str, role_id: int) -> None:
        """移除用户的角色

        Args:
            user_id: 用户ID
            role_id: 角色ID
        """
        ...

    async def user_has_role(self, user_id: str, role_name: str) -> bool:
        """检查用户是否拥有指定角色

        Args:
            user_id: 用户ID
            role_name: 角色名称

        Returns:
            是否拥有该角色
        """
        ...

    async def update(self, role: Role) -> Role:
        """更新角色信息

        Args:
            role: 角色对象

        Returns:
            更新后的角色
        """
        ...

    async def delete(self, role_id: int) -> bool:
        """删除角色

        Args:
            role_id: 角色ID

        Returns:
            删除是否成功
        """
        ...

    async def exists_by_name(self, name: str) -> bool:
        """检查角色名是否已存在

        Args:
            name: 角色名称

        Returns:
            是否存在
        """
        ...

    async def count_users_with_role(self, role_id: int) -> int:
        """统计拥有该角色的用户数

        Args:
            role_id: 角色ID

        Returns:
            用户数量
        """
        ...


class PermissionRepository(Protocol):
    """权限仓储协议

    定义权限数据持久化的接口契约。
    支持权限的CRUD操作和角色权限关联管理。
    """

    async def create(self, permission: Permission) -> Permission:
        """创建新权限

        Args:
            permission: 权限对象

        Returns:
            创建后的权限（含ID）
        """
        ...

    async def get_by_id(self, permission_id: int) -> Permission | None:
        """根据ID获取权限

        Args:
            permission_id: 权限ID

        Returns:
            权限对象，不存在返回None
        """
        ...

    async def get_by_resource_action(
        self, resource: str, action: str
    ) -> Permission | None:
        """根据资源和操作获取权限

        Args:
            resource: 资源类型
            action: 操作类型

        Returns:
            权限对象，不存在返回None
        """
        ...

    async def list_all(self) -> list[Permission]:
        """获取所有权限

        Returns:
            权限列表
        """
        ...

    async def get_role_permissions(self, role_id: int) -> list[Permission]:
        """获取角色的所有权限

        Args:
            role_id: 角色ID

        Returns:
            权限列表
        """
        ...

    async def get_user_permissions(self, user_id: str) -> list[Permission]:
        """获取用户的所有权限（通过角色）

        Args:
            user_id: 用户ID

        Returns:
            权限列表
        """
        ...

    async def assign_permission_to_role(self, role_id: int, permission_id: int) -> None:
        """为角色分配权限

        Args:
            role_id: 角色ID
            permission_id: 权限ID
        """
        ...

    async def remove_permission_from_role(
        self, role_id: int, permission_id: int
    ) -> None:
        """移除角色的权限

        Args:
            role_id: 角色ID
            permission_id: 权限ID
        """
        ...

    async def check_user_permission(
        self, user_id: str, resource: str, action: str
    ) -> bool:
        """检查用户是否拥有指定权限

        Args:
            user_id: 用户ID
            resource: 资源类型
            action: 操作类型

        Returns:
            是否拥有该权限
        """
        ...

    async def update(self, permission: Permission) -> Permission | None:
        """更新权限信息

        Args:
            permission: 权限对象

        Returns:
            更新后的权限，不存在返回None
        """
        ...

    async def delete(self, permission_id: int) -> bool:
        """删除权限

        Args:
            permission_id: 权限ID

        Returns:
            删除是否成功
        """
        ...
