import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    创建一个可供所有测试使用的 TestClient 实例。
    scope="session" 表示这个 fixture 在整个测试会话中只会执行一次。
    """
    with TestClient(app) as test_client:
        yield test_client
