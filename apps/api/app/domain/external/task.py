"""任务管理协议模块

本模块定义异步任务执行的接口协议。

主要组件:
- TaskRunner: 任务运行器抽象基类，负责任务执行和资源管理
- Task: 任务协议，定义任务的操作接口

用于实现长时间运行的异步任务、流式处理等场景。
"""

from abc import ABC, abstractmethod
from typing import Optional, Protocol

from app.domain.external.message_queue import MessageQueue


class TaskRunner(ABC):
    """任务运行器抽象基类

    负责任务的执行、生命周期管理和资源释放。
    实现类需要处理具体的任务执行逻辑。
    """

    @abstractmethod
    async def invoke(self, task: "Task") -> None:
        """执行任务

        Args:
            task: 要执行的任务对象
        """
        raise NotImplementedError

    @abstractmethod
    async def destroy(self) -> None:
        """销毁运行器并释放资源

        包括关闭网络连接、释放内存、清理临时文件等。
        """
        raise NotImplementedError

    @abstractmethod
    async def on_done(self, task: "Task") -> None:
        """任务完成回调

        任务执行完成时调用，可用于清理和后处理。

        Args:
            task: 已完成的任务对象
        """
        raise NotImplementedError


class Task(Protocol):
    """任务协议

    定义任务的操作接口，包括执行、取消、
    输入输出流访问等功能。
    """

    async def invoke(self) -> None:
        """运行当前任务"""
        ...

    def cancel(self) -> bool:
        """取消当前任务

        Returns:
            取消是否成功
        """
        ...

    @property
    def input_stream(self) -> MessageQueue:
        """获取任务的输入流"""
        ...

    @property
    def output_stream(self) -> MessageQueue:
        """获取任务的输出流"""
        ...

    @property
    def id(self) -> str:
        """获取任务ID"""
        ...

    @property
    def done(self) -> bool:
        """获取任务是否已完成"""
        ...

    @classmethod
    def get(cls, task_id: str) -> Optional["Task"]:
        """根据任务ID获取任务实例

        Args:
            task_id: 任务ID

        Returns:
            任务实例，不存在返回None
        """
        ...

    @classmethod
    def create(cls, task_runner: TaskRunner) -> "Task":
        """创建新任务

        Args:
            task_runner: 任务运行器实例

        Returns:
            创建的任务实例
        """
        ...

    @classmethod
    async def destroy(cls) -> None:
        """销毁所有任务实例"""
        ...
