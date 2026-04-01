"""
事件领域模型模块

定义应用中所有事件类型，用于 LLM 与应用之间的消息流转。
主要事件包括：规划事件、步骤事件、消息事件、工具事件等。
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field

from app.domain.models.plan import Plan, Step


class PlanEventStatus(str, Enum):
    """规划事件状态枚举"""

    CREATED = "created"  # 已创建
    UPDATED = "updated"  # 已更新
    COMPLETED = "completed"  # 已完成


class StepEventStatus(str, Enum):
    """步骤事件状态枚举"""

    STARTED = "started"  # 已开始
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class ToolEventStatus(str, Enum):
    """工具事件状态枚举"""

    CALLING = "calling"  # 调用中
    CALLED = "called"  # 调用完毕


class BaseEvent(BaseModel):
    """
    基础事件类型

    所有事件的公共字段：
    - id: 事件唯一标识符
    - type: 事件类型名称（子类中用 Literal 限制具体值）
    - created_at: 事件创建时间
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""  # 事件类型，子类通过 Literal 限制为固定值
    created_at: datetime = Field(default_factory=datetime.now)


class PlanEvent(BaseEvent):
    """规划事件，包含完整的任务规划信息"""

    type: Literal["plan"] = "plan"  # 事件类型标识
    plan: Plan  # 规划内容
    status: PlanEventStatus = PlanEventStatus.CREATED  # 规划状态


class TitleEvent(BaseEvent):
    """标题事件，用于更新或生成任务标题"""

    type: Literal["title"] = "title"  # 事件类型标识
    title: str = ""  # 标题内容


class StepEvent(BaseEvent):
    """步骤事件，代表任务执行中的单个步骤"""

    type: Literal["step"] = "step"  # 事件类型标识
    step: Step  # 步骤详情
    status: StepEventStatus = StepEventStatus.STARTED  # 步骤状态


class MessageEvent(BaseEvent):
    """
    消息事件，承载人类消息或 AI 助手消息

    Attributes:
        role: 消息发送者角色，"user" 表示用户，"assistant" 表示 AI
        message: 消息文本内容
        attachments: 附件列表（如图片、文件等）
    """

    type: Literal["message"] = "message"  # 事件类型标识
    role: Literal["user", "assistant"] = "assistant"  # 消息角色
    message: str = ""  # 消息文本
    attachments: list[str] = Field(default_factory=list)  # 附件 URL 列表


# ==================== 工具内容类型 ====================


class BrowserToolContent(BaseModel):
    """浏览器工具扩展内容，包含页面截图"""

    screenshot: str  # 截图的 Base64 编码或 URL


class SearchToolContent(BaseModel):
    """搜索工具扩展内容，包含搜索结果列表"""

    results: list[Any]  # 搜索结果列表（结构可变）


class ShellToolContent(BaseModel):
    """Shell 工具扩展内容，包含命令执行结果"""

    console: Any  # 控制台输出（可能是文本或结构化数据）


class FileToolContent(BaseModel):
    """文件工具扩展内容，包含文件操作结果"""

    content: str  # 文件内容


class MCPToolContent(BaseModel):
    """MCP (Model Context Protocol) 工具扩展内容"""

    result: Any  # MCP 工具调用结果


class A2AToolContent(BaseModel):
    """A2A (Agent-to-Agent) 智能体工具扩展内容"""

    a2a_result: Any  # A2A 智能体调用结果


# 工具内容的联合类型，支持多种工具扩展
ToolContent = Union[
    BrowserToolContent,
    SearchToolContent,
    ShellToolContent,
    FileToolContent,
    MCPToolContent,
    A2AToolContent,
]


class ToolEvent(BaseEvent):
    """
    工具调用事件，记录 LLM 调用工具的完整过程

    生命周期：
    1. CALLING - 刚发起调用，function_args 填充参数
    2. CALLED - 调用完成，function_result 填充结果
    """

    type: Literal["tool"] = "tool"  # 事件类型标识
    tool_call_id: str  # 工具调用的唯一标识
    tool_name: str  # 工具所属的工具箱/工具集名称
    tool_content: ToolContent | None = None  # 工具扩展内容（可选）
    function_name: str  # 被调用的函数/工具名称
    function_args: dict[str, Any]  # 函数调用参数
    function_result: str | None = None  # 函数执行结果（文本形式）
    status: ToolEventStatus = ToolEventStatus.CALLING  # 当前状态


class WaitEvent(BaseEvent):
    """等待确认事件，暂停执行等待用户输入确认"""

    type: Literal["wait"] = "wait"  # 事件类型标识


class ErrorEvent(BaseEvent):
    """错误事件，记录执行过程中的错误"""

    type: Literal["error"] = "error"  # 事件类型标识
    error: str = ""  # 错误描述信息


class DoneEvent(BaseEvent):
    """完成事件，标志任务/流程执行结束"""

    type: Literal["done"] = "done"  # 事件类型标识


# ==================== 应用事件联合类型 ====================

Event = Annotated[
    PlanEvent
    | TitleEvent
    | StepEvent
    | MessageEvent
    | ToolEvent
    | WaitEvent
    | ErrorEvent
    | DoneEvent,
    Field(discriminator="type"),
]
"""
应用事件联合类型（Discriminated Union）

用途：
    用于 LLM 返回或外部系统传入事件的类型安全解析。

工作原理：
    - Pydantic 根据 "type" 字段的值自动识别具体事件类型
    - 例如：{"type": "tool", ...} → ToolEvent 实例
    - 例如：{"type": "message", ...} → MessageEvent 实例

用法示例：
    event: Event = Event.model_validate(data)  # 自动解析为正确子类
"""

__all__ = [
    "PlanEventStatus",
    "StepEventStatus",
    "ToolEventStatus",
    "BaseEvent",
    "PlanEvent",
    "TitleEvent",
    "StepEvent",
    "MessageEvent",
    "BrowserToolContent",
    "SearchToolContent",
    "ShellToolContent",
    "FileToolContent",
    "MCPToolContent",
    "A2AToolContent",
    "ToolContent",
    "ToolEvent",
    "WaitEvent",
    "ErrorEvent",
    "DoneEvent",
    "Event",
]
