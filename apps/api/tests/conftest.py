"""测试配置和共享 fixtures

提供测试所需的通用 fixtures，包括：
- TestClient 实例（需要 Python 3.12+）
- Mock 依赖
- 测试数据工厂

注意：此项目使用 Python 3.12+ 的泛型语法（PEP 695），
在 Python 3.11 环境下，只有不依赖 app 模块的纯单元测试可以运行。
"""

import sys
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

# Python 版本检查
PYTHON_312_PLUS = sys.version_info >= (3, 12)


def _skip_if_not_py312() -> None:
    """如果不是 Python 3.12+，跳过测试"""
    if not PYTHON_312_PLUS:
        pytest.skip("需要 Python 3.12+ 才能导入 app 模块")


# ==================== TestClient Fixture ====================


@pytest.fixture(scope="module")
def client() -> Generator:
    """创建 TestClient 实例

    使用 module scope 在每个测试模块中复用同一个客户端。
    TestClient 会自动处理 lifespan 事件。
    """
    _skip_if_not_py312()

    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


# ==================== Mock User Fixtures ====================


@pytest.fixture
def mock_user() -> Any:
    """创建测试用户"""
    _skip_if_not_py312()
    from app.domain.models.user import User

    return User(
        id="test-user-id-123",
        email="test@example.com",
        username="testuser",
        is_active=True,
        is_verified=True,
        must_change_password=False,
        last_login_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        roles=[],
    )


@pytest.fixture
def mock_user_with_password() -> Any:
    """创建带密码的测试用户"""
    _skip_if_not_py312()
    from app.domain.models.user import UserWithPassword

    return UserWithPassword(
        id="test-user-id-123",
        email="test@example.com",
        username="testuser",
        password_hash="$2b$12$hashed_password_here",
        is_active=True,
        is_verified=True,
        must_change_password=False,
        last_login_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        roles=[],
    )


@pytest.fixture
def mock_admin_user() -> Any:
    """创建管理员测试用户"""
    _skip_if_not_py312()
    from app.domain.models.user import Permission, Role, User

    admin_permission = Permission(
        id=1,
        resource="*",
        action="*",
        display_name="全部权限",
        created_at=datetime.now(UTC),
    )
    admin_role = Role(
        id=1,
        name="admin",
        display_name="管理员",
        description="系统管理员",
        created_at=datetime.now(UTC),
        permissions=[admin_permission],
    )
    return User(
        id="admin-user-id-123",
        email="admin@example.com",
        username="admin",
        is_active=True,
        is_verified=True,
        must_change_password=False,
        last_login_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        roles=[admin_role],
    )


@pytest.fixture
def mock_role() -> Any:
    """创建测试角色"""
    _skip_if_not_py312()
    from app.domain.models.user import Role

    return Role(
        id=1,
        name="user",
        display_name="普通用户",
        description="普通用户角色",
        created_at=datetime.now(UTC),
        permissions=[],
    )


@pytest.fixture
def mock_permission() -> Any:
    """创建测试权限"""
    _skip_if_not_py312()
    from app.domain.models.user import Permission

    return Permission(
        id=1,
        resource="user",
        action="read",
        display_name="查看用户",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_health_status_ok() -> Any:
    """创建健康状态 - 正常"""
    _skip_if_not_py312()
    from app.domain.models.health_status import HealthStatus

    return HealthStatus(
        service="test-service",
        status="ok",
        details="",
    )


@pytest.fixture
def mock_health_status_error() -> Any:
    """创建健康状态 - 异常"""
    _skip_if_not_py312()
    from app.domain.models.health_status import HealthStatus

    return HealthStatus(
        service="test-service",
        status="error",
        details="连接失败",
    )


# ==================== Repository Mocks ====================


@pytest.fixture
def mock_user_repository() -> AsyncMock:
    """创建 UserRepository mock"""
    mock = AsyncMock()
    mock.create = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.get_by_email = AsyncMock()
    mock.get_by_username = AsyncMock()
    mock.update = AsyncMock()
    mock.update_password = AsyncMock()
    mock.update_last_login = AsyncMock()
    mock.update_verified_status = AsyncMock()
    mock.delete = AsyncMock()
    mock.list_users = AsyncMock()
    mock.count = AsyncMock()
    mock.exists_by_email = AsyncMock()
    mock.exists_by_username = AsyncMock()
    return mock


@pytest.fixture
def mock_role_repository() -> AsyncMock:
    """创建 RoleRepository mock"""
    mock = AsyncMock()
    mock.create = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.get_by_name = AsyncMock()
    mock.list_all = AsyncMock()
    mock.get_user_roles = AsyncMock()
    mock.assign_role_to_user = AsyncMock()
    mock.remove_role_from_user = AsyncMock()
    mock.user_has_role = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    mock.exists_by_name = AsyncMock()
    mock.count_users_with_role = AsyncMock()
    return mock


@pytest.fixture
def mock_permission_repository() -> AsyncMock:
    """创建 PermissionRepository mock"""
    mock = AsyncMock()
    mock.create = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.get_by_resource_action = AsyncMock()
    mock.list_all = AsyncMock()
    mock.get_role_permissions = AsyncMock()
    mock.get_user_permissions = AsyncMock()
    mock.assign_permission_to_role = AsyncMock()
    mock.remove_permission_from_role = AsyncMock()
    mock.check_user_permission = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def mock_audit_log_repository() -> AsyncMock:
    """创建 AuditLogRepository mock"""
    mock = AsyncMock()
    mock.create = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.list_by_user = AsyncMock()
    mock.list_by_resource = AsyncMock()
    return mock


# ==================== External Service Mocks ====================


@pytest.fixture
def mock_session_manager() -> AsyncMock:
    """创建 SessionManager mock"""
    mock = AsyncMock()
    mock.create_session = AsyncMock(return_value="session-id-123")
    mock.get_session = AsyncMock()
    mock.delete_session = AsyncMock()
    mock.delete_user_sessions = AsyncMock()
    mock.set_verification_token = AsyncMock()
    mock.get_verification_token = AsyncMock()
    mock.delete_verification_token = AsyncMock()
    mock.add_to_blacklist = AsyncMock()
    mock.is_blacklisted = AsyncMock(return_value=False)
    return mock


@pytest.fixture
def mock_email_sender() -> AsyncMock:
    """创建 EmailSender mock"""
    mock = AsyncMock()
    mock.send_verification_email = AsyncMock()
    mock.send_welcome_email = AsyncMock()
    mock.send_password_reset_email = AsyncMock()
    return mock


@pytest.fixture
def mock_rate_limiter() -> AsyncMock:
    """创建 RateLimiter mock"""
    mock = AsyncMock()
    mock.check_rate_limit = AsyncMock(return_value=True)
    mock.check_rate_limit_or_raise = AsyncMock()
    mock.get_remaining_requests = AsyncMock(return_value=10)
    mock.reset_rate_limit = AsyncMock()
    mock.get_ttl = AsyncMock(return_value=60)
    return mock


@pytest.fixture
def mock_health_checker() -> AsyncMock:
    """创建 HealthChecker mock"""
    _skip_if_not_py312()
    from app.domain.models.health_status import HealthStatus

    mock = AsyncMock()
    mock.check = AsyncMock(
        return_value=HealthStatus(service="mock", status="ok", details="")
    )
    return mock
