"""状态路由端点测试

测试 /api/status 端点的各种场景：
- 正常情况：所有服务健康
- 异常情况：部分服务不健康
- 边界情况：空响应等

注意：此测试需要 Python 3.12+ 才能运行，因为 app 模块使用 PEP 695 泛型语法。
"""

import sys
from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest

# Python 版本检查
PYTHON_312_PLUS = sys.version_info >= (3, 12)


def _skip_if_not_py312() -> None:
    """如果不是 Python 3.12+，跳过测试"""
    if not PYTHON_312_PLUS:
        pytest.skip("需要 Python 3.12+ 才能导入 app 模块")


class TestStatusRoutes:
    """状态路由测试类"""

    @pytest.fixture
    def mock_status_service(self) -> AsyncMock:
        """创建 mock StatusService"""
        _skip_if_not_py312()
        from app.application.services.status_service import StatusService

        return AsyncMock(spec=StatusService)

    @pytest.fixture
    def test_client_with_override(
        self, mock_status_service: AsyncMock
    ) -> Generator:
        """创建带依赖覆盖的 TestClient"""
        _skip_if_not_py312()
        from fastapi.testclient import TestClient

        from app.interfaces.service_dependencies import get_health_checker_service
        from app.main import app

        # 使用 FastAPI 的依赖覆盖机制
        app.dependency_overrides[get_health_checker_service] = (
            lambda: mock_status_service
        )
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
        # 清理依赖覆盖
        app.dependency_overrides.clear()

    def test_status_routes_success(
        self,
        test_client_with_override,
        mock_status_service: AsyncMock,
    ) -> None:
        """测试健康检查成功场景

        当所有服务正常时，应返回 200 状态码和成功消息。
        """
        _skip_if_not_py312()
        from app.domain.models.health_status import HealthStatus

        mock_statuses = [
            HealthStatus(service="mysql", status="ok", details=""),
            HealthStatus(service="redis", status="ok", details=""),
        ]
        mock_status_service.check_all = AsyncMock(return_value=mock_statuses)

        response = test_client_with_override.get("/api/status")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "系统健康检查成功"
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2

    def test_status_routes_partial_failure(
        self,
        test_client_with_override,
        mock_status_service: AsyncMock,
    ) -> None:
        """测试部分服务不健康场景

        当存在服务异常时，应返回 200 HTTP状态码但 code=503。
        """
        _skip_if_not_py312()
        from app.domain.models.health_status import HealthStatus

        mock_statuses = [
            HealthStatus(service="mysql", status="ok", details=""),
            HealthStatus(service="redis", status="error", details="连接超时"),
        ]
        mock_status_service.check_all = AsyncMock(return_value=mock_statuses)

        response = test_client_with_override.get("/api/status")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 503
        assert "异常" in data["message"]
        assert isinstance(data["data"], list)

    def test_status_routes_all_services_down(
        self,
        test_client_with_override,
        mock_status_service: AsyncMock,
    ) -> None:
        """测试所有服务不健康场景"""
        _skip_if_not_py312()
        from app.domain.models.health_status import HealthStatus

        mock_statuses = [
            HealthStatus(service="mysql", status="error", details="连接失败"),
            HealthStatus(service="redis", status="error", details="连接拒绝"),
        ]
        mock_status_service.check_all = AsyncMock(return_value=mock_statuses)

        response = test_client_with_override.get("/api/status")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 503

    def test_status_routes_empty_checkers(
        self,
        test_client_with_override,
        mock_status_service: AsyncMock,
    ) -> None:
        """测试没有健康检查器的场景"""
        _skip_if_not_py312()

        mock_status_service.check_all = AsyncMock(return_value=[])

        response = test_client_with_override.get("/api/status")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        # Response.success() 会将空列表（falsy值）转换为空字典
        assert data["data"] == {} or data["data"] == []

    def test_status_response_structure(
        self,
        test_client_with_override,
        mock_status_service: AsyncMock,
    ) -> None:
        """测试响应数据结构符合预期"""
        _skip_if_not_py312()
        from app.domain.models.health_status import HealthStatus

        mock_statuses = [
            HealthStatus(service="mysql", status="ok", details="版本: 8.0"),
        ]
        mock_status_service.check_all = AsyncMock(return_value=mock_statuses)

        response = test_client_with_override.get("/api/status")

        data = response.json()

        # 验证顶层响应结构
        assert "code" in data
        assert "message" in data
        assert "data" in data

        # 验证健康状态数据结构
        if data["data"]:
            health_item = data["data"][0]
            assert "service" in health_item
            assert "status" in health_item
            assert "details" in health_item
