"""Redis Stream 消息队列实现模块

本模块提供基于 Redis Stream 的消息队列功能实现，用于异步任务处理和事件驱动场景。

主要功能:
- 消息的发布（追加到 Stream）
- 消息的消费（阻塞/非阻塞读取）
- 消息的删除
- 队列状态查询（空判断、长度）

存储结构:
- Stream Key: stream_name（由构造时指定）
- 消息格式: Field-Value 对

技术特点:
- 使用 Redis Stream 数据结构，支持持久化和高吞吐量
- 支持消费者组实现多消费者负载均衡
- 内置分布式锁机制，保证消息操作的原子性
"""

import asyncio
import logging
import uuid
from typing import Any

from app.domain.external.message_queue import MessageQueue
from app.infrastructure.storage.redis import get_redis_client

logger = logging.getLogger(__name__)


class RedisStreamMessageQueue(MessageQueue):
    """基于 Redis Stream 的消息队列实现

    实现 MessageQueue 接口协议，提供高性能的异步消息队列功能。
    使用 Redis Stream 作为底层存储，支持消息持久化和多消费者场景。

    Attributes:
        _stream_name: Redis Stream 的键名
        _redis: Redis 客户端实例
        _lock_expire_seconds: 分布式锁的过期时间（秒）
    """

    def __init__(self, stream_name: str) -> None:
        """初始化 Redis Stream 消息队列

        Args:
            stream_name: Redis Stream 的键名，用于标识消息队列
        """
        self._stream_name = stream_name
        self._redis = get_redis_client()
        self._lock_expire_seconds = 10

    async def _acquire_lock(
        self, lock_key: str, timeout_seconds: int = 5
    ) -> str | None:
        """尝试获取分布式锁

        使用 Redis SET NX EX 命令实现简单的分布式锁。
        锁值使用 UUID4 生成，确保唯一性。

        流程:
        1. 生成唯一的锁值（UUID4）
        2. 循环尝试设置锁，直到超时或成功
        3. 使用 SET NX EX 保证原子性（键不存在时才设置，并设置过期时间）

        Args:
            lock_key: 锁的键名
            timeout_seconds: 获取锁的超时时间（秒），默认 5 秒

        Returns:
            str | None: 成功获取锁时返回锁值，失败时返回 None
        """
        # 1.创建锁的值
        lock_value = str(uuid.uuid4())
        end_time = timeout_seconds

        # 2.使用end_time构建循环
        while end_time > 0:
            # 3.使用redis的set方法，将lock_key和lock_value存储到redis中，并且设置过期时间
            result = await self._redis.client.set(
                lock_key,
                lock_value,
                nx=True,  # 如果值存在则不设置，否则进行设置
                ex=self._lock_expire_seconds,
            )

            # 4.如果设置成功，则返回锁的值
            if result:
                return lock_value

            # 5.睡眠指定时间并且将end_time递减
            await asyncio.sleep(0.1)
            end_time -= 0.1
        return None

    async def _release_lock(self, lock_key: str, lock_value: str) -> bool:
        """释放分布式锁

        使用 Lua 脚本实现原子性的锁释放操作。
        只有锁值匹配时才执行删除，防止误删其他客户端的锁。

        流程:
        1. 构建 Lua 脚本：比较锁值，匹配则删除
        2. 注册脚本到 Redis
        3. 执行脚本并传递键和参数

        Args:
            lock_key: 锁的键名
            lock_value: 锁的值（用于验证所有权）

        Returns:
            bool: 释放成功返回 True，失败返回 False
        """
        # 1.构建一段redis的脚本用于释放分布式锁
        release_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """

        try:
            # 2.注册脚本
            script = self._redis.client.register_script(release_script)

            # 3.执行脚本并传递keys+args释放分布式锁
            result = await script(keys=[lock_key], args=[lock_value])

            return result == 1
        except Exception:
            return False

    async def put(self, message: Any) -> str:
        """往消息队列中添加一条消息

        Args:
            message: 消息内容（任意可序列化对象）

        Returns:
            str: 消息ID
        """
        logger.debug(f"往消息队列[{self._stream_name}]中添加一条消息: {message}")

        return await self._redis.client.xadd(self._stream_name, {"data": message})

    async def get(
        self, start_id: str | None = None, block_ms: int | None = None
    ) -> tuple[str, Any]:
        """获取一条消息

        从消息队列中读取一条消息，支持阻塞和非阻塞两种模式。

        Args:
            start_id: 起始消息ID（不包含），None 表示从最新消息开始
            block_ms: 阻塞等待时间（毫秒），None 表示非阻塞模式

        Returns:
            tuple[str, Any]: 元组 (消息ID, 消息内容)，无消息时返回 (None, None)
        """
        logger.debug(f"从消息队列[{self._stream_name}]中获取一条消息: {start_id}")
        # 1.判断start_id是否为None
        if start_id is None:
            start_id = "0"

        # 2.从redis流中获取一条数据
        messages = await self._redis.client.xread(
            {self._stream_name: start_id},
            count=1,
            block=block_ms,
        )

        # 3.检查messages是否存在
        if not messages:
            return None, None

        # 4.从消息列表中取出对应的消息数据
        stream_messages = messages[0][1]
        if not stream_messages:
            return None, None

        # 5.提取id和数据
        message_id, message_data = stream_messages[0]

        try:
            return message_id, message_data.get("data")
        except Exception as e:
            logger.error(f"从消息队列[{self._stream_name}]获取数据失败: {str(e)}")
            return None, None

    async def pop(self) -> tuple[str, Any]:
        """获取并移除队列中的第一条消息

        使用分布式锁保证原子性，防止多消费者同时获取同一条消息。

        流程:
        1. 获取分布式锁
        2. 从 Stream 中获取第一条消息（XREAD 或 XRANGE）
        3. 删除已读取的消息（XDEL）
        4. 释放分布式锁

        Returns:
            tuple[str, Any]: 元组 (消息ID, 消息内容)，无消息时返回 (None, None)
        """
        # 1.记录日志
        logger.debug(f"从消息队列[{self._stream_name}]中弹出第一条消息")
        lock_key = f"lock:{self._stream_name}:pop"

        # 2.构建分布式锁，如果分布式锁创建失败则返回None
        lock_value = await self._acquire_lock(lock_key)
        if not lock_value:
            return None, None

        try:
            # 3.从redis流中获取第一条消息
            messages = await self._redis.client.xrange(
                self._stream_name, "-", "+", count=1
            )
            if not messages:
                return None, None

            # 4.取出消息id和消息
            message_id, message_data = messages[0]

            # 5.删除消息队列中的message数据
            await self._redis.client.xdel(self._stream_name, message_id)

            return message_id, message_data.get("data")
        except Exception as e:
            logger.error(f"解析消息队列[{self._stream_name}]出错: {str(e)}")
            return None
        finally:
            await self._release_lock(lock_key, lock_value)

    async def clear(self) -> None:
        """清空消息队列中的所有消息

        使用 XTRIM 命令删除 Stream 中的所有消息。
        """
        await self._redis.client.xtrim(self._stream_name, 0)

    async def is_empty(self) -> bool:
        """判断消息队列是否为空

        Returns:
            bool: 队列为空返回 True，否则返回 False
        """
        return self.size() == 0

    async def size(self) -> int:
        """获取消息队列的长度

        Returns:
            int: 队列中的消息数量
        """
        return await self._redis.client.xlen(self._stream_name)

    async def delete_message(self, message_id: str) -> bool:
        """删除指定的消息

        Args:
            message_id: 消息ID

        Returns:
            bool: 删除成功返回 True，失败返回 False
        """
        try:
            await self._redis.client.xdel(self._stream_name, message_id)
            return True
        except Exception:
            return False

    async def get_latest_id(self) -> str:
        """获取消息队列中最新的消息ID

        使用 XREVRANGE 命令按 ID 倒序获取最新消息。

        Returns:
            str: 最新消息的ID，无消息时返回 "0"
        """
        # 1.取出倒序的消息列表，并且设置count=1
        messages = await self._redis.client.xrevrange(
            self._stream_name, "+", "-", count=1
        )
        if not messages:
            return "0"

        # 2.否则取出消息id并返回
        return messages[0][0]
