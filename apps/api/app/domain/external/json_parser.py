"""外部服务协议模块"""

from typing import Any, Protocol


class JSONParser(Protocol):
    """JSON解析器协议"""

    async def invoke(
        self, text: str, default_value: Any | None = None
    ) -> dict | list | Any:
        """解析JSON字符串"""
        ...
