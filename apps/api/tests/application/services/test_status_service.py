"""状态服务测试

测试 StatusService 的健康检查功能：
- 正常情况
- 异常处理
- 并发检查
"""

from unittest.mock import AsyncMock

import pytest

from app.application.services.status_service import StatusService
from app.domain.models.health_status import HealthStatus


class TestStatusService:
    """状态服务测试"""

    @pytest.fixture
    def mock_healthy_checker(self) -> AsyncMock:
        """创建健康的检查器 mock"""
        checker = AsyncMock()
        checker.check = AsyncMock(
            return_value=HealthStatus(
                service="test-service",
                status="ok",
                details="",
            )
        )
        return checker

    @pytest.fixture
    def mock_unhealthy_checker(self) -> AsyncMock:
        """创建不健康的检查器 mock"""
        checker = AsyncMock()
        checker.check = AsyncMock(
            return_value=HealthStatus(
                service="test-service",
                status="error",
                details="连接失败",
            )
        )
        return checker

    @pytest.fixture
    def mock_failing_checker(self) -> AsyncMock:
        """创建抛出异常的检查器 mock"""
        checker = AsyncMock()
        checker.check = AsyncMock(side_effect=Exception("检查器内部错误"))
        return checker

    @pytest.mark.asyncio
    async def test_check_all_single_healthy(
        self, mock_healthy_checker: AsyncMock
    ) -> None:
        """测试单个健康检查器"""
        service = StatusService(checkers=[mock_healthy_checker])

        results = await service.check_all()

        assert len(results) == 1
        assert results[0].status == "ok"
        mock_healthy_checker.check.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_all_multiple_healthy(
        self, mock_healthy_checker: AsyncMock
    ) -> None:
        """测试多个健康检查器"""
        checker1 = AsyncMock()
        checker1.check = AsyncMock(
            return_value=HealthStatus(service="mysql", status="ok", details="")
        )
        checker2 = AsyncMock()
        checker2.check = AsyncMock(
            return_value=HealthStatus(service="redis", status="ok", details="")
        )

        service = StatusService(checkers=[checker1, checker2])

        results = await service.check_all()

        assert len(results) == 2
        assert all(r.status == "ok" for r in results)

    @pytest.mark.asyncio
    async def test_check_all_mixed_status(
        self,
        mock_healthy_checker: AsyncMock,
        mock_unhealthy_checker: AsyncMock,
    ) -> None:
        """测试混合健康状态"""
        service = StatusService(checkers=[mock_healthy_checker, mock_unhealthy_checker])

        results = await service.check_all()

        assert len(results) == 2
        statuses = [r.status for r in results]
        assert "ok" in statuses
        assert "error" in statuses

    @pytest.mark.asyncio
    async def test_check_all_with_exception(
        self,
        mock_healthy_checker: AsyncMock,
        mock_failing_checker: AsyncMock,
    ) -> None:
        """测试检查器抛出异常的情况"""
        service = StatusService(checkers=[mock_healthy_checker, mock_failing_checker])

        results = await service.check_all()

        assert len(results) == 2
        # 应该有一个是异常处理后的结果
        error_results = [r for r in results if r.status == "error"]
        assert len(error_results) == 1
        assert error_results[0].service == "未知服务"

    @pytest.mark.asyncio
    async def test_check_all_all_failing(self) -> None:
        """测试所有检查器都抛出异常"""
        checker1 = AsyncMock()
        checker1.check = AsyncMock(side_effect=Exception("错误1"))
        checker2 = AsyncMock()
        checker2.check = AsyncMock(side_effect=Exception("错误2"))

        service = StatusService(checkers=[checker1, checker2])

        results = await service.check_all()

        assert len(results) == 2
        assert all(r.status == "error" for r in results)
        assert all(r.service == "未知服务" for r in results)

    @pytest.mark.asyncio
    async def test_check_all_empty_checkers(self) -> None:
        """测试没有检查器的情况"""
        service = StatusService(checkers=[])

        results = await service.check_all()

        assert results == []

    @pytest.mark.asyncio
    async def test_check_all_preserves_service_name(self) -> None:
        """测试保留服务名称"""
        checker = AsyncMock()
        checker.check = AsyncMock(
            return_value=HealthStatus(
                service="custom-service",
                status="ok",
                details="版本 1.0",
            )
        )

        service = StatusService(checkers=[checker])

        results = await service.check_all()

        assert results[0].service == "custom-service"
        assert results[0].details == "版本 1.0"

    @pytest.mark.asyncio
    async def test_check_all_concurrent_execution(self) -> None:
        """测试并发执行检查"""
        import asyncio

        call_times = []

        async def slow_check():
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)
            return HealthStatus(service="slow", status="ok", details="")

        checker1 = AsyncMock()
        checker1.check = slow_check
        checker2 = AsyncMock()
        checker2.check = slow_check

        service = StatusService(checkers=[checker1, checker2])

        start = asyncio.get_event_loop().time()
        await service.check_all()
        duration = asyncio.get_event_loop().time() - start

        # 如果是并发执行，总时间应该接近 0.1 秒而不是 0.2 秒
        assert duration < 0.15
