"""记忆管理领域模型模块

本模块定义Agent记忆系统的核心领域模型。

主要模型:
- Memory: Agent记忆模型，用于存储和管理对话历史

领域规则:
- 记忆采用消息列表形式存储，每条消息为字典格式
- 支持消息的添加、获取、回滚和压缩操作
"""

import logging
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class Memory(BaseModel):
    """记忆信息，定义agent的记忆信息"""

    messages: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def get_message_role(cls, message: dict[str, Any]) -> str:
        """根据传递的消息来获取消息的角色信息

        Args:
            message: 消息字典，包含role字段

        Returns:
            消息角色字符串，如 'user'、'assistant'、'tool'
        """
        return message.get("role")

    def add_message(self, message: dict[str, Any]) -> None:
        """往记忆中添加一条消息

        Args:
            message: 消息字典，包含role、content等字段
        """
        self.messages.append(message)

    def add_messages(self, messages: list[dict[str, Any]]) -> None:
        """往记忆中添加多条消息

        Args:
            messages: 消息字典列表
        """
        self.messages.extend(messages)

    def get_messages(self) -> list[dict[str, Any]]:
        """获取记忆中的所有消息列表

        Returns:
            所有消息的字典列表
        """
        return self.messages

    def get_last_message(self) -> Optional[dict[str, Any]]:
        """获取记忆中的最后一条消息，如果不存在则返回None

        Returns:
            最后一条消息字典，不存在则返回None
        """
        return self.messages[-1] if len(self.messages) > 0 else None

    def roll_back(self) -> None:
        """回滚记忆，删除最后一条消息"""
        self.messages = self.messages[:-1]

    def compact(self) -> None:
        """记忆压缩，将记忆中已经执行的工具(搜索/网页源码获取/浏览器访问结果等)这类已经执行过的消息进行压缩检索

        具体压缩规则:
        1. 压缩 browser_view 和 browser_navigate 工具的结果内容为占位符 "(removed)"
        2. 删除 reasoning_content 字段以减少上下文大小
        """
        for message in self.messages:
            if self.get_message_role(message) == "tool":
                if message.get("function_name") in ["browser_view", "browser_navigate"]:
                    message["content"] = "(removed)"
                    logger.debug(f"从记忆中移除对应工具的结果: {message['function_name']}")

            if "reasoning_content" in message:
                logger.debug(f"从记忆中移除工具思考结果: {message['reasoning_content'][:50]}...")
                del message["reasoning_content"]

    @property
    def empty(self) -> bool:
        """只读属性，检查记忆是否为空

        Returns:
            True表示记忆为空，False表示非空
        """
        return len(self.messages) == 0
