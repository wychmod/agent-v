"""消息队列协议模块

本模块定义消息队列服务的接口协议。

用于实现异步任务处理、事件驱动等场景的消息传递机制。
支持消息的发布、消费、删除等操作。
"""

from typing import Any, Protocol


class MessageQueue(Protocol):
    """消息队列协议

    定义消息队列操作的接口契约。
    支持FIFO队列的基本操作。
    """

    async def put(self, message: Any) -> str:
        """往消息队列中添加一条消息

        Args:
            message: 消息内容（任意可序列化对象）

        Returns:
            消息ID
        """
        ...

    async def get(
        self, start_id: str | None = None, block_ms: int | None = None
    ) -> tuple[str, Any]:
        """获取一条消息

        Args:
            start_id: 起始消息ID（不包含）
            block_ms: 阻塞等待时间（毫秒）

        Returns:
            元组 (消息ID, 消息内容)
        """
        ...

    async def pop(self) -> tuple[str, Any]:
        """获取并移除队列中的第一条消息

        Returns:
            元组 (消息ID, 消息内容)
        """
        ...

    async def clear(self) -> None:
        """清空消息队列中的所有消息"""
        ...

    async def is_empty(self) -> bool:
        """判断消息队列是否为空

        Returns:
            True表示队列为空
        """
        ...

    async def size(self) -> int:
        """获取消息队列的长度

        Returns:
            队列中的消息数量
        """
        ...

    async def delete_message(self, message_id: str) -> bool:
        """删除指定的消息

        Args:
            message_id: 消息ID

        Returns:
            删除是否成功
        """
        ...
