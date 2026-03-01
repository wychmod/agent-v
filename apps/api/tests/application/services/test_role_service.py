"""角色服务测试

测试 RoleService 的角色和权限管理功能：
- 角色 CRUD
- 权限 CRUD
- 角色权限分配
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.errors.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from app.application.services.role_service import RoleService
from app.domain.models.user import Permission, Role, User


class TestRoleServiceCreateRole:
    """创建角色功能测试"""

    @pytest.fixture
    def role_service(
        self,
        mock_role_repository: AsyncMock,
        mock_permission_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
    ) -> RoleService:
        """创建角色服务实例"""
        return RoleService(
            role_repository=mock_role_repository,
            permission_repository=mock_permission_repository,
            audit_log_repository=mock_audit_log_repository,
        )

    @pytest.mark.asyncio
    async def test_create_role_success(
        self,
        role_service: RoleService,
        mock_role_repository: AsyncMock,
        mock_admin_user: User,
    ) -> None:
        """测试创建角色成功"""
        mock_role_repository.exists_by_name.return_value = False
        mock_role_repository.create.return_value = Role(
            id=1,
            name="editor",
            display_name="编辑者",
            description="编辑者角色",
            created_at=datetime.now(UTC),
        )

        role = await role_service.create_role(
            name="editor",
            display_name="编辑者",
            description="编辑者角色",
            current_user=mock_admin_user,
        )

        assert role.name == "editor"
        mock_role_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_role_name_exists(
        self,
        role_service: RoleService,
        mock_role_repository: AsyncMock,
        mock_admin_user: User,
    ) -> None:
        """测试角色名已存在"""
        mock_role_repository.exists_by_name.return_value = True

        with pytest.raises(ConflictError) as exc_info:
            await role_service.create_role(
                name="admin",
                display_name="管理员",
                description=None,
                current_user=mock_admin_user,
            )

        assert "已存在" in exc_info.value.message


class TestRoleServiceUpdateRole:
    """更新角色功能测试"""

    @pytest.fixture
    def role_service(
        self,
        mock_role_repository: AsyncMock,
        mock_permission_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
    ) -> RoleService:
        """创建角色服务实例"""
        return RoleService(
            role_repository=mock_role_repository,
            permission_repository=mock_permission_repository,
            audit_log_repository=mock_audit_log_repository,
        )

    @pytest.mark.asyncio
    async def test_update_role_success(
        self,
        role_service: RoleService,
        mock_role_repository: AsyncMock,
        mock_admin_user: User,
        mock_role: Role,
    ) -> None:
        """测试更新角色成功"""
        mock_role_repository.get_by_id.return_value = mock_role
        mock_role_repository.update.return_value = mock_role

        role = await role_service.update_role(
            role_id=1,
            display_name="新显示名",
            description="新描述",
            current_user=mock_admin_user,
        )

        mock_role_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_role_not_found(
        self,
        role_service: RoleService,
        mock_role_repository: AsyncMock,
        mock_admin_user: User,
    ) -> None:
        """测试更新不存在的角色"""
        mock_role_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await role_service.update_role(
                role_id=999,
                display_name="新名称",
                description=None,
                current_user=mock_admin_user,
            )

        assert "角色" in exc_info.value.message


class TestRoleServiceDeleteRole:
    """删除角色功能测试"""

    @pytest.fixture
    def role_service(
        self,
        mock_role_repository: AsyncMock,
        mock_permission_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
    ) -> RoleService:
        """创建角色服务实例"""
        return RoleService(
            role_repository=mock_role_repository,
            permission_repository=mock_permission_repository,
            audit_log_repository=mock_audit_log_repository,
        )

    @pytest.mark.asyncio
    async def test_delete_role_success(
        self,
        role_service: RoleService,
        mock_role_repository: AsyncMock,
        mock_admin_user: User,
    ) -> None:
        """测试删除角色成功"""
        custom_role = Role(
            id=10,
            name="custom_role",
            display_name="自定义角色",
            description=None,
            created_at=datetime.now(UTC),
        )
        mock_role_repository.get_by_id.return_value = custom_role
        mock_role_repository.count_users_with_role.return_value = 0
        mock_role_repository.delete.return_value = True

        result = await role_service.delete_role(
            role_id=10,
            current_user=mock_admin_user,
        )

        assert result is True
        mock_role_repository.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_role_not_found(
        self,
        role_service: RoleService,
        mock_role_repository: AsyncMock,
        mock_admin_user: User,
    ) -> None:
        """测试删除不存在的角色"""
        mock_role_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await role_service.delete_role(
                role_id=999,
                current_user=mock_admin_user,
            )

    @pytest.mark.asyncio
    async def test_delete_system_role(
        self,
        role_service: RoleService,
        mock_role_repository: AsyncMock,
        mock_admin_user: User,
    ) -> None:
        """测试删除系统保留角色（应失败）"""
        admin_role = Role(
            id=1,
            name="admin",
            display_name="管理员",
            description=None,
            created_at=datetime.now(UTC),
        )
        mock_role_repository.get_by_id.return_value = admin_role

        with pytest.raises(BadRequestError) as exc_info:
            await role_service.delete_role(
                role_id=1,
                current_user=mock_admin_user,
            )

        assert "系统保留角色" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_delete_role_with_users(
        self,
        role_service: RoleService,
        mock_role_repository: AsyncMock,
        mock_admin_user: User,
    ) -> None:
        """测试删除有用户关联的角色（应失败）"""
        custom_role = Role(
            id=10,
            name="custom_role",
            display_name="自定义角色",
            description=None,
            created_at=datetime.now(UTC),
        )
        mock_role_repository.get_by_id.return_value = custom_role
        mock_role_repository.count_users_with_role.return_value = 5

        with pytest.raises(BadRequestError) as exc_info:
            await role_service.delete_role(
                role_id=10,
                current_user=mock_admin_user,
            )

        assert "用户关联" in exc_info.value.message


class TestRoleServicePermission:
    """权限管理功能测试"""

    @pytest.fixture
    def role_service(
        self,
        mock_role_repository: AsyncMock,
        mock_permission_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
    ) -> RoleService:
        """创建角色服务实例"""
        return RoleService(
            role_repository=mock_role_repository,
            permission_repository=mock_permission_repository,
            audit_log_repository=mock_audit_log_repository,
        )

    @pytest.mark.asyncio
    async def test_list_all_permissions(
        self,
        role_service: RoleService,
        mock_permission_repository: AsyncMock,
        mock_permission: Permission,
    ) -> None:
        """测试获取所有权限"""
        mock_permission_repository.list_all.return_value = [mock_permission]

        permissions = await role_service.list_all_permissions()

        assert len(permissions) == 1
        mock_permission_repository.list_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_permission_success(
        self,
        role_service: RoleService,
        mock_permission_repository: AsyncMock,
        mock_admin_user: User,
    ) -> None:
        """测试创建权限成功"""
        mock_permission_repository.get_by_resource_action.return_value = None
        mock_permission_repository.create.return_value = Permission(
            id=1,
            resource="article",
            action="publish",
            display_name="发布文章",
            created_at=datetime.now(UTC),
        )

        permission = await role_service.create_permission(
            resource="article",
            action="publish",
            display_name="发布文章",
            current_user=mock_admin_user,
        )

        assert permission.resource == "article"
        assert permission.action == "publish"

    @pytest.mark.asyncio
    async def test_create_permission_exists(
        self,
        role_service: RoleService,
        mock_permission_repository: AsyncMock,
        mock_admin_user: User,
        mock_permission: Permission,
    ) -> None:
        """测试创建已存在的权限"""
        mock_permission_repository.get_by_resource_action.return_value = mock_permission

        with pytest.raises(ConflictError) as exc_info:
            await role_service.create_permission(
                resource="user",
                action="read",
                display_name="查看用户",
                current_user=mock_admin_user,
            )

        assert "已存在" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_update_permission_success(
        self,
        role_service: RoleService,
        mock_permission_repository: AsyncMock,
        mock_admin_user: User,
        mock_permission: Permission,
    ) -> None:
        """测试更新权限成功"""
        mock_permission_repository.get_by_id.return_value = mock_permission
        mock_permission_repository.update.return_value = mock_permission

        permission = await role_service.update_permission(
            permission_id=1,
            display_name="新显示名",
            current_user=mock_admin_user,
        )

        mock_permission_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_permission_not_found(
        self,
        role_service: RoleService,
        mock_permission_repository: AsyncMock,
        mock_admin_user: User,
    ) -> None:
        """测试更新不存在的权限"""
        mock_permission_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await role_service.update_permission(
                permission_id=999,
                display_name="新名称",
                current_user=mock_admin_user,
            )

    @pytest.mark.asyncio
    async def test_delete_permission_success(
        self,
        role_service: RoleService,
        mock_permission_repository: AsyncMock,
        mock_admin_user: User,
        mock_permission: Permission,
    ) -> None:
        """测试删除权限成功"""
        mock_permission_repository.get_by_id.return_value = mock_permission
        mock_permission_repository.delete.return_value = True

        result = await role_service.delete_permission(
            permission_id=1,
            current_user=mock_admin_user,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_remove_permission_from_role_success(
        self,
        role_service: RoleService,
        mock_role_repository: AsyncMock,
        mock_permission_repository: AsyncMock,
        mock_admin_user: User,
        mock_role: Role,
        mock_permission: Permission,
    ) -> None:
        """测试移除角色权限成功"""
        mock_role_repository.get_by_id.return_value = mock_role
        mock_permission_repository.get_by_id.return_value = mock_permission

        await role_service.remove_permission_from_role(
            role_id=1,
            permission_id=1,
            current_user=mock_admin_user,
        )

        mock_permission_repository.remove_permission_from_role.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_permission_from_role_role_not_found(
        self,
        role_service: RoleService,
        mock_role_repository: AsyncMock,
        mock_admin_user: User,
    ) -> None:
        """测试从不存在的角色移除权限"""
        mock_role_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await role_service.remove_permission_from_role(
                role_id=999,
                permission_id=1,
                current_user=mock_admin_user,
            )

        assert "角色" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_remove_permission_from_role_permission_not_found(
        self,
        role_service: RoleService,
        mock_role_repository: AsyncMock,
        mock_permission_repository: AsyncMock,
        mock_admin_user: User,
        mock_role: Role,
    ) -> None:
        """测试移除不存在的权限"""
        mock_role_repository.get_by_id.return_value = mock_role
        mock_permission_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await role_service.remove_permission_from_role(
                role_id=1,
                permission_id=999,
                current_user=mock_admin_user,
            )

        assert "权限" in exc_info.value.message
