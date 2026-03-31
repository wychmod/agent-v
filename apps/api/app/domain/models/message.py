"""消息领域模型模块"""

from pydantic import BaseModel, Field


class Message(BaseModel):
    """消息模型

    Attributes:
        message: 消息内容
        attachments: 用户发送的附件列表
    """

    message: str = ""
    attachments: list[str] = Field(default_factory=list)
