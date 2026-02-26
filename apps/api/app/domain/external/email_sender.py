"""邮件发送协议"""

from typing import Protocol


class EmailSender(Protocol):
    """邮件发送协议，定义邮件发送的接口契约"""

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True,
    ) -> bool:
        """发送邮件"""
        ...

    async def send_verification_email(
        self,
        to: str,
        username: str,
        verification_url: str,
    ) -> bool:
        """发送邮箱验证邮件"""
        ...

    async def send_password_reset_email(
        self,
        to: str,
        username: str,
        reset_url: str,
    ) -> bool:
        """发送密码重置邮件"""
        ...

    async def send_welcome_email(
        self,
        to: str,
        username: str,
    ) -> bool:
        """发送欢迎邮件"""
        ...
