"""用户领域模型测试

测试 User、Role、Permission 等领域模型的行为：
- 模型属性
- 业务方法
- 边界条件
"""

from datetime import UTC, datetime

import pytest

from app.domain.models.user import (
    AuditLog,
    Permission,
    Role,
    SessionData,
    User,
    UserWithPassword,
)


class TestPermission:
    """权限模型测试"""

    def test_permission_creation(self) -> None:
        """测试权限创建"""
        permission = Permission(
            id=1,
            resource="user",
            action="read",
            display_name="查看用户",
            created_at=datetime.now(UTC),
        )

        assert permission.id == 1
        assert permission.resource == "user"
        assert permission.action == "read"
        assert permission.display_name == "查看用户"

    def test_get_full_name(self) -> None:
        """测试获取完整权限标识"""
        permission = Permission(
            id=1,
            resource="user",
            action="create",
            display_name="创建用户",
            created_at=datetime.now(UTC),
        )

        assert permission.get_full_name() == "user:create"

    def test_get_full_name_special_characters(self) -> None:
        """测试资源名含特殊字符的情况"""
        permission = Permission(
            id=1,
            resource="api-endpoint",
            action="execute",
            display_name="执行API",
            created_at=datetime.now(UTC),
        )

        assert permission.get_full_name() == "api-endpoint:execute"


class TestRole:
    """角色模型测试"""

    def test_role_creation_without_permissions(self) -> None:
        """测试创建无权限角色"""
        role = Role(
            id=1,
            name="guest",
            display_name="访客",
            description="访客角色",
            created_at=datetime.now(UTC),
        )

        assert role.id == 1
        assert role.name == "guest"
        assert role.permissions == []

    def test_role_creation_with_permissions(self) -> None:
        """测试创建带权限角色"""
        permission = Permission(
            id=1,
            resource="user",
            action="read",
            display_name="查看用户",
            created_at=datetime.now(UTC),
        )
        role = Role(
            id=1,
            name="viewer",
            display_name="查看者",
            description=None,
            created_at=datetime.now(UTC),
            permissions=[permission],
        )

        assert len(role.permissions) == 1
        assert role.permissions[0].resource == "user"


class TestUser:
    """用户模型测试"""

    @pytest.fixture
    def sample_permission(self) -> Permission:
        """创建测试权限"""
        return Permission(
            id=1,
            resource="user",
            action="read",
            display_name="查看用户",
            created_at=datetime.now(UTC),
        )

    @pytest.fixture
    def sample_role(self, sample_permission: Permission) -> Role:
        """创建测试角色"""
        return Role(
            id=1,
            name="admin",
            display_name="管理员",
            description="系统管理员",
            created_at=datetime.now(UTC),
            permissions=[sample_permission],
        )

    @pytest.fixture
    def sample_user(self, sample_role: Role) -> User:
        """创建测试用户"""
        return User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            roles=[sample_role],
        )

    def test_user_creation(self) -> None:
        """测试用户创建"""
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=False,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.roles == []

    def test_has_role_returns_true(self, sample_user: User) -> None:
        """测试用户拥有指定角色"""
        assert sample_user.has_role("admin") is True

    def test_has_role_returns_false(self, sample_user: User) -> None:
        """测试用户没有指定角色"""
        assert sample_user.has_role("superadmin") is False

    def test_has_role_empty_roles(self) -> None:
        """测试无角色用户"""
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            roles=[],
        )

        assert user.has_role("admin") is False

    def test_has_permission_returns_true(self, sample_user: User) -> None:
        """测试用户拥有指定权限"""
        assert sample_user.has_permission("user", "read") is True

    def test_has_permission_returns_false(self, sample_user: User) -> None:
        """测试用户没有指定权限"""
        assert sample_user.has_permission("user", "delete") is False
        assert sample_user.has_permission("system", "read") is False

    def test_has_permission_empty_roles(self) -> None:
        """测试无角色用户的权限"""
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            roles=[],
        )

        assert user.has_permission("user", "read") is False

    def test_get_all_permissions(self, sample_user: User) -> None:
        """测试获取所有权限"""
        permissions = sample_user.get_all_permissions()

        assert isinstance(permissions, list)
        assert "user:read" in permissions

    def test_get_all_permissions_multiple_roles(self) -> None:
        """测试多角色用户的权限合并"""
        perm1 = Permission(
            id=1,
            resource="user",
            action="read",
            display_name="查看用户",
            created_at=datetime.now(UTC),
        )
        perm2 = Permission(
            id=2,
            resource="user",
            action="write",
            display_name="编辑用户",
            created_at=datetime.now(UTC),
        )
        role1 = Role(
            id=1,
            name="reader",
            display_name="读者",
            description=None,
            created_at=datetime.now(UTC),
            permissions=[perm1],
        )
        role2 = Role(
            id=2,
            name="writer",
            display_name="编辑者",
            description=None,
            created_at=datetime.now(UTC),
            permissions=[perm2],
        )
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            roles=[role1, role2],
        )

        permissions = user.get_all_permissions()

        assert len(permissions) == 2
        assert "user:read" in permissions
        assert "user:write" in permissions

    def test_get_all_permissions_deduplication(self) -> None:
        """测试权限去重"""
        perm = Permission(
            id=1,
            resource="user",
            action="read",
            display_name="查看用户",
            created_at=datetime.now(UTC),
        )
        role1 = Role(
            id=1,
            name="role1",
            display_name="角色1",
            description=None,
            created_at=datetime.now(UTC),
            permissions=[perm],
        )
        role2 = Role(
            id=2,
            name="role2",
            display_name="角色2",
            description=None,
            created_at=datetime.now(UTC),
            permissions=[perm],
        )
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            roles=[role1, role2],
        )

        permissions = user.get_all_permissions()

        # 应该去重
        assert len(permissions) == 1

    def test_to_safe_dict(self) -> None:
        """测试安全字典输出"""
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        safe_dict = user.to_safe_dict()

        assert "id" in safe_dict
        assert "email" in safe_dict
        assert "password_hash" not in safe_dict


class TestUserWithPassword:
    """带密码用户模型测试"""

    def test_user_with_password_creation(self) -> None:
        """测试带密码用户创建"""
        user = UserWithPassword(
            id="user-123",
            email="test@example.com",
            username="testuser",
            password_hash="$2b$12$hashedpassword",
            is_active=True,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert user.password_hash == "$2b$12$hashedpassword"

    def test_user_with_password_inherits_user(self) -> None:
        """测试继承 User 的所有方法"""
        user = UserWithPassword(
            id="user-123",
            email="test@example.com",
            username="testuser",
            password_hash="$2b$12$hashedpassword",
            is_active=True,
            is_verified=True,
            must_change_password=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert user.has_role("admin") is False
        assert user.get_all_permissions() == []


class TestAuditLog:
    """审计日志模型测试"""

    def test_audit_log_creation(self) -> None:
        """测试审计日志创建"""
        log = AuditLog(
            user_id="user-123",
            action="login",
            resource="user",
            resource_id="user-123",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            status="success",
        )

        assert log.user_id == "user-123"
        assert log.action == "login"
        assert log.status == "success"

    def test_audit_log_optional_fields(self) -> None:
        """测试审计日志可选字段"""
        log = AuditLog(
            action="system_check",
            resource="system",
        )

        assert log.user_id is None
        assert log.ip_address is None
        assert log.details is None

    def test_audit_log_with_details(self) -> None:
        """测试审计日志详情字段"""
        log = AuditLog(
            user_id="user-123",
            action="update_profile",
            resource="user",
            resource_id="user-123",
            status="success",
            details={"old_username": "old", "new_username": "new"},
        )

        assert log.details is not None
        assert log.details["old_username"] == "old"


class TestSessionData:
    """会话数据模型测试"""

    def test_session_data_creation(self) -> None:
        """测试会话数据创建"""
        session = SessionData(
            user_id="user-123",
            roles=["admin", "user"],
            permissions=["user:read", "user:write"],
            ip_address="192.168.1.1",
            user_agent="Chrome/120",
            login_at=datetime.now(UTC),
        )

        assert session.user_id == "user-123"
        assert "admin" in session.roles
        assert "user:read" in session.permissions

    def test_session_data_default_values(self) -> None:
        """测试会话数据默认值"""
        session = SessionData(
            user_id="user-123",
            login_at=datetime.now(UTC),
        )

        assert session.roles == []
        assert session.permissions == []
        assert session.ip_address is None
