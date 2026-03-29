"""规划管理领域模型模块

本模块定义Agent任务规划系统的核心领域模型。

主要模型:
- ExecutionStatus: 任务执行状态枚举
- Step: 计划中的单个步骤/子任务
- Plan: 任务规划模型，用于存储用户消息拆分出的子任务

领域规则:
- 规划状态包括：空闲/等待中、执行中、执行完成、失败
- 每个步骤有独立的状态，当步骤完成或失败时标记为done
- Plan通过get_next_step方法获取下一个待执行的步骤
"""

import logging
import uuid
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """规划/任务执行的状态枚举

    Attributes:
        PENDING: 空闲或等待中
        RUNNING: 执行中
        COMPLETED: 执行完成
        FAILED: 失败
    """

    PENDING = "pending"  # 空闲or等待中
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"  # 失败


class Step(BaseModel):
    """计划中的每一个步骤/子任务

    Attributes:
        id: 子任务的唯一标识符
        description: 步骤的描述信息
        status: 子任务的执行状态
        result: 步骤执行后的结果内容
        error: 步骤执行失败时的错误信息
        success: 步骤是否执行成功
        attachments: 附件列表信息
        done: 只读属性，步骤是否已结束（完成或失败）
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # 子任务id
    description: str = ""  # 步骤的描述信息
    status: ExecutionStatus = ExecutionStatus.PENDING  # 子任务的执行状态
    result: str | None = None  # 结果
    error: str | None = None  # 错误信息
    success: bool = False  # 是否执行成功
    attachments: list[str] = Field(default_factory=list)  # 附件列表信息

    model_config = ConfigDict(from_attributes=True)

    @property
    def done(self) -> bool:
        """只读属性，返回步骤是否结束

        Returns:
            True表示步骤已完成或失败，False表示正在执行或等待
        """
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]


class Plan(BaseModel):
    """规划Domain模型，用于存储用户传递消息拆分出来的子任务/子步骤

    Attributes:
        id: 计划的唯一标识符
        title: 任务标题
        goal: 任务目标描述
        language: 工作语言
        steps: 步骤列表/子任务列表
        message: AI传递的原始消息内容
        status: 规划的整体执行状态
        error: 规划执行失败时的错误信息
        done: 只读属性，判断计划是否结束
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # 计划id
    title: str = ""  # 任务标题
    goal: str = ""  # 任务目标
    language: str = ""  # 工作语言
    steps: list["Step"] = Field(default_factory=list)  # 步骤列表/子任务列表
    message: str = ""  # AI传递的消息
    status: ExecutionStatus = ExecutionStatus.PENDING  # 规划的状态
    error: str | None = None  # 错误信息

    model_config = ConfigDict(from_attributes=True)

    @property
    def done(self) -> bool:
        """只读属性，用于判断计划是否结束

        Returns:
            True表示计划已完成或失败，False表示正在执行或等待
        """
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]

    def get_next_step(self) -> Step | None:
        """获取需要执行的下一个步骤

        遍历步骤列表，返回第一个未结束（未完成且未失败）的步骤。

        Returns:
            下一个待执行的步骤对象，如果所有步骤都已结束则返回None
        """
        return next((step for step in self.steps if not step.done), None)
