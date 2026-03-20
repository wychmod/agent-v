"""邮件发送协议模块

本模块定义邮件发送服务的接口协议。

支持多种邮件场景:
- 通用邮件发送
- 邮箱验证邮件
- 密码重置邮件
- 欢迎邮件

具体实现可以使用SMTP、第三方邮件服务等。
"""

from typing import Protocol


class EmailSender(Protocol):
    """邮件发送协议

    定义邮件发送的接口契约。
    实现类需要处理邮件模板渲染和发送逻辑。
    """

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True,
    ) -> bool:
        """发送通用邮件

        Args:
            to: 收件人邮箱
            subject: 邮件主题
            body: 邮件正文
            html: 是否为HTML格式

        Returns:
            发送是否成功
        """
        ...

    async def send_verification_email(
        self,
        to: str,
        username: str,
        verification_url: str,
    ) -> bool:
        """发送邮箱验证邮件

        Args:
            to: 收件人邮箱
            username: 用户名（用于邮件个性化）
            verification_url: 验证链接

        Returns:
            发送是否成功
        """
        ...

    async def send_password_reset_email(
        self,
        to: str,
        username: str,
        reset_url: str,
    ) -> bool:
        """发送密码重置邮件

        Args:
            to: 收件人邮箱
            username: 用户名
            reset_url: 重置密码链接

        Returns:
            发送是否成功
        """
        ...

    async def send_welcome_email(
        self,
        to: str,
        username: str,
    ) -> bool:
        """发送欢迎邮件

        用户完成邮箱验证后发送。

        Args:
            to: 收件人邮箱
            username: 用户名

        Returns:
            发送是否成功
        """
        ...
