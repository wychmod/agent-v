"""用户服务测试

测试 UserService 的用户管理功能：
- 获取用户
- 更新用户
- 修改密码
- 角色分配
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.errors.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.application.security.password_handler import PasswordHandler
from app.application.services.user_service import UserService
from app.domain.models.user import Role, User, UserWithPassword


class TestUserServiceGetUser:
    """获取用户功能测试"""

    @pytest.fixture
    def user_service(
        self,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_permission_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
    ) -> UserService:
        """创建用户服务实例"""
        return UserService(
            user_repository=mock_user_repository,
            role_repository=mock_role_repository,
            permission_repository=mock_permission_repository,
            audit_log_repository=mock_audit_log_repository,
        )

    @pytest.mark.asyncio
    async def test_get_user_success(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """测试获取用户成功"""
        mock_user_repository.get_by_id.return_value = mock_user

        user = await user_service.get_user("test-user-id-123")

        assert user.id == mock_user.id
        assert user.email == mock_user.email
        mock_user_repository.get_by_id.assert_called_once_with("test-user-id-123")

    @pytest.mark.asyncio
    async def test_get_user_not_found(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """测试用户不存在"""
        mock_user_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await user_service.get_user("nonexistent-user")

        assert "用户" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_user_with_password: UserWithPassword,
    ) -> None:
        """测试通过邮箱获取用户"""
        mock_user_repository.get_by_email.return_value = mock_user_with_password

        user = await user_service.get_user_by_email("test@example.com")

        assert user.email == "test@example.com"
        # 返回的用户不应包含密码哈希
        assert (
            not hasattr(user, "password_hash")
            or "password_hash" not in user.model_dump()
        )


class TestUserServiceUpdateProfile:
    """更新用户资料功能测试"""

    @pytest.fixture
    def user_service(
        self,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_permission_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
    ) -> UserService:
        """创建用户服务实例"""
        return UserService(
            user_repository=mock_user_repository,
            role_repository=mock_role_repository,
            permission_repository=mock_permission_repository,
            audit_log_repository=mock_audit_log_repository,
        )

    @pytest.mark.asyncio
    async def test_update_profile_own_user(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """测试用户更新自己的资料"""
        mock_user_repository.get_by_id.return_value = mock_user
        mock_user_repository.exists_by_username.return_value = False
        mock_user_repository.update.return_value = mock_user

        updated_user = await user_service.update_profile(
            user_id=mock_user.id,
            username="newusername",
            current_user=mock_user,
        )

        mock_user_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_admin_updates_other(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_user: User,
        mock_admin_user: User,
    ) -> None:
        """测试管理员更新其他用户资料"""
        mock_user_repository.get_by_id.return_value = mock_user
        mock_user_repository.exists_by_username.return_value = False
        mock_user_repository.update.return_value = mock_user

        updated_user = await user_service.update_profile(
            user_id=mock_user.id,
            username="newusername",
            current_user=mock_admin_user,
        )

        mock_user_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_non_admin_updates_other(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """测试非管理员更新其他用户资料（应失败）"""
        other_user = User(
            id="other-user-id",
            email="other@example.com",
            username="otheruser",
            is_active=True,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            roles=[],
        )
        mock_user_repository.get_by_id.return_value = other_user

        with pytest.raises(ForbiddenError):
            await user_service.update_profile(
                user_id="other-user-id",
                username="newusername",
                current_user=mock_user,
            )

    @pytest.mark.asyncio
    async def test_update_profile_username_conflict(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """测试用户名冲突"""
        mock_user_repository.get_by_id.return_value = mock_user
        mock_user_repository.exists_by_username.return_value = True

        with pytest.raises(ConflictError) as exc_info:
            await user_service.update_profile(
                user_id=mock_user.id,
                username="existingname",
                current_user=mock_user,
            )

        assert "用户名已被使用" in exc_info.value.message


class TestUserServiceChangePassword:
    """修改密码功能测试"""

    @pytest.fixture
    def mock_password_handler(self) -> MagicMock:
        """创建 mock 密码处理器"""
        handler = MagicMock(spec=PasswordHandler)
        handler.verify_password.return_value = True
        handler.hash_password.return_value = "$2b$12$newhash"
        handler.validate_password_or_raise.return_value = None
        return handler

    @pytest.fixture
    def user_service(
        self,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_permission_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
        mock_password_handler: MagicMock,
    ) -> UserService:
        """创建用户服务实例"""
        return UserService(
            user_repository=mock_user_repository,
            role_repository=mock_role_repository,
            permission_repository=mock_permission_repository,
            audit_log_repository=mock_audit_log_repository,
            password_handler=mock_password_handler,
        )

    @pytest.mark.asyncio
    async def test_change_password_success(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_user: User,
        mock_user_with_password: UserWithPassword,
    ) -> None:
        """测试修改密码成功"""
        mock_user_repository.get_by_id.return_value = mock_user
        mock_user_repository.get_by_email.return_value = mock_user_with_password

        await user_service.change_password(
            user_id=mock_user.id,
            old_password="OldPassword123!",
            new_password="NewPassword123!",
        )

        mock_user_repository.update_password.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_user: User,
        mock_user_with_password: UserWithPassword,
        mock_password_handler: MagicMock,
    ) -> None:
        """测试原密码错误"""
        mock_user_repository.get_by_id.return_value = mock_user
        mock_user_repository.get_by_email.return_value = mock_user_with_password
        mock_password_handler.verify_password.return_value = False

        with pytest.raises(ForbiddenError) as exc_info:
            await user_service.change_password(
                user_id=mock_user.id,
                old_password="WrongPassword!",
                new_password="NewPassword123!",
            )

        # ForbiddenError 在提供 resource 和 action 时会生成标准消息
        assert "密码" in exc_info.value.message or "权限" in exc_info.value.message


class TestUserServiceRoleManagement:
    """角色管理功能测试"""

    @pytest.fixture
    def user_service(
        self,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_permission_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
    ) -> UserService:
        """创建用户服务实例"""
        return UserService(
            user_repository=mock_user_repository,
            role_repository=mock_role_repository,
            permission_repository=mock_permission_repository,
            audit_log_repository=mock_audit_log_repository,
        )

    @pytest.mark.asyncio
    async def test_assign_role_success(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_user: User,
        mock_admin_user: User,
        mock_role: Role,
    ) -> None:
        """测试分配角色成功"""
        mock_user_repository.get_by_id.return_value = mock_user
        mock_role_repository.get_by_name.return_value = mock_role

        await user_service.assign_role(
            user_id=mock_user.id,
            role_name="user",
            current_user=mock_admin_user,
        )

        mock_role_repository.assign_role_to_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_role_user_not_found(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_admin_user: User,
    ) -> None:
        """测试分配角色给不存在的用户"""
        mock_user_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await user_service.assign_role(
                user_id="nonexistent",
                role_name="user",
                current_user=mock_admin_user,
            )

        assert "用户" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_assign_role_role_not_found(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_user: User,
        mock_admin_user: User,
    ) -> None:
        """测试分配不存在的角色"""
        mock_user_repository.get_by_id.return_value = mock_user
        mock_role_repository.get_by_name.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await user_service.assign_role(
                user_id=mock_user.id,
                role_name="nonexistent_role",
                current_user=mock_admin_user,
            )

        assert "角色" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_remove_role_success(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_user: User,
        mock_admin_user: User,
        mock_role: Role,
    ) -> None:
        """测试移除角色成功"""
        mock_user_repository.get_by_id.return_value = mock_user
        mock_role_repository.get_by_name.return_value = mock_role

        await user_service.remove_role(
            user_id=mock_user.id,
            role_name="user",
            current_user=mock_admin_user,
        )

        mock_role_repository.remove_role_from_user.assert_called_once()


class TestUserServiceListUsers:
    """用户列表功能测试"""

    @pytest.fixture
    def user_service(
        self,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_permission_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
    ) -> UserService:
        """创建用户服务实例"""
        return UserService(
            user_repository=mock_user_repository,
            role_repository=mock_role_repository,
            permission_repository=mock_permission_repository,
            audit_log_repository=mock_audit_log_repository,
        )

    @pytest.mark.asyncio
    async def test_list_users(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_user: User,
    ) -> None:
        """测试获取用户列表"""
        mock_user_repository.list_users.return_value = [mock_user]
        mock_user_repository.count.return_value = 1

        users, total = await user_service.list_users(skip=0, limit=20)

        assert len(users) == 1
        assert total == 1
        mock_user_repository.list_users.assert_called_once_with(0, 20, None)

    @pytest.mark.asyncio
    async def test_list_users_with_filter(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
    ) -> None:
        """测试带过滤条件的用户列表"""
        mock_user_repository.list_users.return_value = []
        mock_user_repository.count.return_value = 0

        users, total = await user_service.list_users(skip=0, limit=20, is_active=True)

        mock_user_repository.list_users.assert_called_once_with(0, 20, True)


class TestUserServiceDeleteUser:
    """删除用户功能测试"""

    @pytest.fixture
    def user_service(
        self,
        mock_user_repository: AsyncMock,
        mock_role_repository: AsyncMock,
        mock_permission_repository: AsyncMock,
        mock_audit_log_repository: AsyncMock,
    ) -> UserService:
        """创建用户服务实例"""
        return UserService(
            user_repository=mock_user_repository,
            role_repository=mock_role_repository,
            permission_repository=mock_permission_repository,
            audit_log_repository=mock_audit_log_repository,
        )

    @pytest.mark.asyncio
    async def test_delete_user_success(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_user: User,
        mock_admin_user: User,
    ) -> None:
        """测试删除用户成功"""
        mock_user_repository.get_by_id.return_value = mock_user
        mock_user_repository.delete.return_value = True

        result = await user_service.delete_user(
            user_id=mock_user.id,
            current_user=mock_admin_user,
        )

        assert result is True
        mock_user_repository.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_self(
        self,
        user_service: UserService,
        mock_admin_user: User,
    ) -> None:
        """测试不能删除自己"""
        with pytest.raises(ForbiddenError) as exc_info:
            await user_service.delete_user(
                user_id=mock_admin_user.id,
                current_user=mock_admin_user,
            )

        # ForbiddenError 在提供 resource 和 action 时会生成标准消息
        assert "用户" in exc_info.value.message or "权限" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_delete_user_not_found(
        self,
        user_service: UserService,
        mock_user_repository: AsyncMock,
        mock_admin_user: User,
    ) -> None:
        """测试删除不存在的用户"""
        mock_user_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await user_service.delete_user(
                user_id="nonexistent",
                current_user=mock_admin_user,
            )
