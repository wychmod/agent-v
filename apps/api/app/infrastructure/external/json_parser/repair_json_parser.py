"""JSON解析器实现模块"""

import logging
from typing import Any

import json_repair

from app.domain.external.json_parser import JSONParser

logger = logging.getLogger(__name__)


class RepairJSONParser(JSONParser):
    """JSON解析器实现，使用json_repair库解析和修复JSON字符串"""

    async def invoke(
        self, text: str, default_value: Any | None = None
    ) -> dict | list | Any:
        """解析JSON字符串，支持修复格式错误

        Args:
            text: 要解析的JSON字符串
            default_value: 解析失败时返回的默认值

        Returns:
            解析后的字典或列表

        Raises:
            ValueError: 文本为空且无默认值时抛出
        """
        logger.info(f"RepairJSONParser invoke: {text}")
        if not text or not text.strip():
            if default_value is None:
                raise ValueError("json文本为空，且无默认值")
            return default_value
        return json_repair.repair_json(text, ensure_ascii=False, return_objects=True)
