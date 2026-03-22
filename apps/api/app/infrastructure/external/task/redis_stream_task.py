"""Redis Stream 任务实现模块

本模块提供基于 Redis Stream 的异步任务功能实现。

主要功能:
- 异步任务的创建、执行、取消
- 任务输入/输出流管理
- 任务注册与查找

架构设计:
- 使用 Redis Stream 作为任务输入输出的传输通道
- 每个任务有独立的输入流和输出流
- 全局任务注册表支持通过任务ID查找任务实例

存储结构:
- task:input:{task_id} -> 任务输入流
- task:output:{task_id} -> 任务输出流

"""

import asyncio
import logging
import uuid
from typing import Optional

from app.domain.external.message_queue import MessageQueue
from app.domain.external.task import Task, TaskRunner
from app.infrastructure.external.message_queue.redis_stream_message_queue import (
    RedisStreamMessageQueue,
)

logger = logging.getLogger(__name__)


class RedisStreamTask(Task):
    """基于 Redis Stream 的任务实现

    实现 Task 接口协议，提供异步任务的管理功能。
    每个任务实例拥有独立的输入/输出流用于数据传输。

    Attributes:
        _task_registry: 全局任务注册表，key 为任务 ID，value 为任务实例
        _task_runner: 任务执行器，负责具体任务逻辑的执行
        _id: 任务唯一标识（UUID4）
        _execution_task: asyncio 内部任务引用，用于跟踪任务状态
        _input_stream: 任务输入流
        _output_stream: 任务输出流
    """

    # 定义一个全局变量用于存储所有已注册的任务
    _task_registry: dict[str, "RedisStreamTask"] = {}

    def __init__(self, task_runner: TaskRunner) -> None:
        """初始化任务实例

        创建一个新的任务实例，并将其注册到全局注册表中。
        同时创建该任务专属的输入流和输出流。

        Args:
            task_runner: 任务执行器，负责处理具体的任务逻辑
        """
        self._task_runner = task_runner
        self._id = str(uuid.uuid4())
        self._execution_task: asyncio.Task | None = None  # 在后台执行的任务

        input_stream_name = f"task:input:{self._id}"
        output_stream_name = f"task:output:{self._id}"

        self._input_stream = RedisStreamMessageQueue(input_stream_name)
        self._output_stream = RedisStreamMessageQueue(output_stream_name)

        # 将当前类实例注册到全局变量中
        RedisStreamTask._task_registry[self._id] = self

    def _cleanup_registry(self) -> None:
        """清除类全局变量中当前注册的任务

        从全局任务注册表中移除当前任务实例。
        通常在任务取消或完成时调用。
        """
        if self._id in RedisStreamTask._task_registry:
            del RedisStreamTask._task_registry[self._id]
            logger.info(f"任务[{self._id}]从注册中心移除")

    def _on_task_done(self) -> None:
        """任务结束时的回调函数

        流程:
        1. 调用 TaskRunner 的 on_done 回调
        2. 从全局注册表中移除当前任务
        """
        # 1.检测task_runner是否存在，如果存在则调用task_runner的回调函数
        if self._task_runner:
            asyncio.create_task(self._task_runner.on_done(self))

        # 2.清除当前任务对应的资源
        self._cleanup_registry()

    async def _execute_task(self) -> None:
        """使用 TaskRunner 执行任务的内部方法

        调用 TaskRunner.invoke 执行具体任务逻辑。
        捕获任务执行过程中的异常并记录日志。
        无论任务成功完成还是异常退出，都会触发 _on_task_done 回调。
        """
        try:
            await self._task_runner.invoke(self)
        except asyncio.CancelledError:
            logger.info(f"任务[{self._id}]执行被取消")
        except Exception as e:
            logger.error(f"任务[{self._id}]执行出现异常: {str(e)}")
        finally:
            self._on_task_done()

    async def invoke(self) -> None:
        """使用提供的 task_runner 来运行任务

        判断任务是否已结束（done），已结束才能重新启动。
        未结束的任务不会重复创建新的执行任务。

        Note:
            done 为 True 的情况：
            1. 任务从未启动（_execution_task is None）
            2. 任务已完成（_execution_task.done() 返回 True）
        """
        if self.done:
            self._execution_task = asyncio.create_task(self._execute_task())
            logger.info(f"任务[{self._id}]开始执行")

    def cancel(self) -> bool:
        """取消当前执行的任务

        如果任务正在执行，则向 asyncio.Task 发送取消信号。
        无论任务是否正在执行，都会从注册表中移除。

        Returns:
            bool: 取消操作总是返回 True
        """
        if not self.done:
            # 1.取消任务
            self._execution_task.cancel()
            logger.info(f"任务[{self._id}]已取消")

            # 2.清除注册的当前任务
            self._cleanup_registry()
            return True

        # 3.否则代表任务已结束，无需重复取消
        self._cleanup_registry()
        return True

    @property
    def input_stream(self) -> MessageQueue:
        """获取任务的输入流

        用于向任务发送输入数据。

        Returns:
            RedisStreamMessageQueue: 任务的输入流队列
        """
        return self._input_stream

    @property
    def output_stream(self) -> MessageQueue:
        """获取任务的输出流

        用于从任务获取输出数据。

        Returns:
            RedisStreamMessageQueue: 任务的输出流队列
        """
        return self._output_stream

    @property
    def id(self) -> str:
        """获取任务ID

        Returns:
            str: 任务的唯一标识符
        """
        return self._id

    @property
    def done(self) -> bool:
        """获取任务是否已完成

        Returns:
            bool: 任务已完成返回 True，未完成返回 False。
                  任务从未启动也被视为已完成。
        """
        if self._execution_task is None:
            return True
        return self._execution_task.done()

    @classmethod
    def get(cls, task_id: str) -> Optional["Task"]:
        """根据任务ID获取任务实例

        Args:
            task_id: 任务ID

        Returns:
            Optional[Task]: 找到则返回任务实例，否则返回 None
        """
        return RedisStreamTask._task_registry.get(task_id)

    @classmethod
    def create(cls, task_runner: TaskRunner) -> "Task":
        """创建新任务

        Args:
            task_runner: 任务运行器实例

        Returns:
            Task: 创建的任务实例
        """
        return cls(task_runner)

    @classmethod
    async def destroy(cls) -> None:
        """销毁所有任务实例

        遍历全局注册表中的所有任务，取消每个任务并调用
        TaskRunner.destroy() 释放资源。最后清空注册表。
        """
        for task_id in RedisStreamTask._task_registry:
            # 1.获取对应的任务
            task = RedisStreamTask._task_registry[task_id]
            task.cancel()

            # 2.检测任务是否有任务运行器
            if task._task_runner:
                await task._task_runner.destroy()

        # 3.清除全局变量
        cls._task_registry.clear()
