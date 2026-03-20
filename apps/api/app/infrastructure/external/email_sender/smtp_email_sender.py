"""SMTP 邮件发送服务实现模块

本模块提供基于 SMTP 协议的邮件发送功能实现，支持多种邮件类型。

主要功能:
- 通用邮件发送（支持 HTML 和纯文本格式）
- 邮箱验证邮件发送
- 密码重置邮件发送
- 欢迎邮件发送

技术特点:
- 使用 aiosmtplib 实现异步发送
- 支持 TLS 加密传输
- 内置美观的 HTML 邮件模板
- 完善的错误处理和日志记录

依赖配置:
- SMTP 服务器地址和端口
- SMTP 认证凭据
- 发件人信息
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.domain.external.email_sender import EmailSender
from core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class SMTPEmailSender(EmailSender):
    """基于 SMTP 协议的邮件发送服务实现

    实现 EmailSender 接口，提供完整的邮件发送功能。
    支持异步发送，内置多种预定义邮件模板。

    Attributes:
        _settings: 应用配置对象，包含 SMTP 服务器配置信息
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """初始化 SMTP 邮件发送器

        Args:
            settings: 可选的配置对象，未提供时使用全局配置
        """
        self._settings = settings or get_settings()

    async def _send(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True,
    ) -> bool:
        """内部邮件发送方法

        流程:
        1. 构建 MIME 邮件消息（设置发件人、收件人、主题）
        2. 根据 html 参数选择邮件格式（HTML 或纯文本）
        3. 通过 aiosmtplib 异步发送邮件
        4. 记录发送结果日志

        Args:
            to: 收件人邮箱地址
            subject: 邮件主题
            body: 邮件正文内容
            html: 是否为 HTML 格式，默认为 True

        Returns:
            bool: 发送成功返回 True，失败返回 False
        """
        try:
            message = MIMEMultipart("alternative")
            message["From"] = (
                f"{self._settings.email_from_name} <{self._settings.email_from}>"
            )
            message["To"] = to
            message["Subject"] = subject

            if html:
                part = MIMEText(body, "html", "utf-8")
            else:
                part = MIMEText(body, "plain", "utf-8")
            message.attach(part)

            await aiosmtplib.send(
                message,
                hostname=self._settings.smtp_host,
                port=self._settings.smtp_port,
                username=self._settings.smtp_user,
                password=self._settings.smtp_password,
                start_tls=self._settings.smtp_use_tls,
            )

            logger.info(f"邮件发送成功: to={to}, subject={subject}")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: to={to}, error={e}")
            return False

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True,
    ) -> bool:
        """发送通用邮件

        提供通用的邮件发送功能，支持自定义主题和内容。

        Args:
            to: 收件人邮箱地址
            subject: 邮件主题
            body: 邮件正文内容
            html: 是否为 HTML 格式，默认为 True

        Returns:
            bool: 发送成功返回 True，失败返回 False
        """
        return await self._send(to, subject, body, html)

    async def send_verification_email(
        self,
        to: str,
        username: str,
        verification_url: str,
    ) -> bool:
        """发送邮箱验证邮件

        流程:
        1. 设置邮件主题为"验证您的邮箱地址"
        2. 使用验证邮件模板生成 HTML 内容
        3. 调用内部发送方法完成发送

        Args:
            to: 收件人邮箱地址
            username: 用户名，用于邮件内容个性化
            verification_url: 验证链接 URL（15分钟有效）

        Returns:
            bool: 发送成功返回 True，失败返回 False
        """
        subject = "验证您的邮箱地址"
        body = self._get_verification_email_template(username, verification_url)
        return await self._send(to, subject, body, html=True)

    async def send_password_reset_email(
        self,
        to: str,
        username: str,
        reset_url: str,
    ) -> bool:
        """发送密码重置邮件

        流程:
        1. 设置邮件主题为"重置您的密码"
        2. 使用密码重置邮件模板生成 HTML 内容
        3. 调用内部发送方法完成发送

        Args:
            to: 收件人邮箱地址
            username: 用户名，用于邮件内容个性化
            reset_url: 密码重置链接 URL（15分钟有效）

        Returns:
            bool: 发送成功返回 True，失败返回 False
        """
        subject = "重置您的密码"
        body = self._get_password_reset_email_template(username, reset_url)
        return await self._send(to, subject, body, html=True)

    async def send_welcome_email(
        self,
        to: str,
        username: str,
    ) -> bool:
        """发送欢迎邮件

        在用户账户成功验证后发送欢迎邮件。

        Args:
            to: 收件人邮箱地址
            username: 用户名，用于邮件内容个性化

        Returns:
            bool: 发送成功返回 True，失败返回 False
        """
        subject = "欢迎加入我们"
        body = self._get_welcome_email_template(username)
        return await self._send(to, subject, body, html=True)

    @staticmethod
    def _get_verification_email_template(username: str, verification_url: str) -> str:
        """生成邮箱验证邮件的 HTML 模板

        模板特点:
        - 蓝色主题头部
        - 清晰的验证按钮
        - 备用链接文本
        - 有效期提示

        Args:
            username: 用户名
            verification_url: 验证链接 URL

        Returns:
            str: 完整的 HTML 邮件内容
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4A90D9; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f9f9f9; }}
        .button {{ display: inline-block; padding: 12px 30px; background: #4A90D9; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>邮箱验证</h1>
        </div>
        <div class="content">
            <p>您好，{username}！</p>
            <p>感谢您的注册。请点击下面的按钮验证您的邮箱地址：</p>
            <p style="text-align: center;">
                <a href="{verification_url}" class="button">验证邮箱</a>
            </p>
            <p>如果按钮无法点击，请复制以下链接到浏览器：</p>
            <p style="word-break: break-all; color: #666;">{verification_url}</p>
            <p>此链接将在 15 分钟后失效。</p>
            <p>如果这不是您的操作，请忽略此邮件。</p>
        </div>
        <div class="footer">
            <p>此邮件由系统自动发送，请勿直接回复。</p>
        </div>
    </div>
</body>
</html>
"""

    @staticmethod
    def _get_password_reset_email_template(username: str, reset_url: str) -> str:
        """生成密码重置邮件的 HTML 模板

        模板特点:
        - 红色警示主题头部
        - 明显的重置按钮
        - 安全提示警告框
        - 备用链接文本

        Args:
            username: 用户名
            reset_url: 密码重置链接 URL

        Returns:
            str: 完整的 HTML 邮件内容
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #E74C3C; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f9f9f9; }}
        .button {{ display: inline-block; padding: 12px 30px; background: #E74C3C; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .warning {{ background: #FFF3CD; border: 1px solid #FFEEBA; padding: 10px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>密码重置</h1>
        </div>
        <div class="content">
            <p>您好，{username}！</p>
            <p>我们收到了重置您密码的请求。请点击下面的按钮设置新密码：</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">重置密码</a>
            </p>
            <p>如果按钮无法点击，请复制以下链接到浏览器：</p>
            <p style="word-break: break-all; color: #666;">{reset_url}</p>
            <p>此链接将在 15 分钟后失效。</p>
            <div class="warning">
                <strong>安全提示：</strong>如果您没有请求重置密码，请忽略此邮件，您的密码将保持不变。
            </div>
        </div>
        <div class="footer">
            <p>此邮件由系统自动发送，请勿直接回复。</p>
        </div>
    </div>
</body>
</html>
"""

    @staticmethod
    def _get_welcome_email_template(username: str) -> str:
        """生成欢迎邮件的 HTML 模板

        模板特点:
        - 绿色成功主题头部
        - 账户激活确认信息
        - 简洁友好的欢迎语

        Args:
            username: 用户名

        Returns:
            str: 完整的 HTML 邮件内容
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #27AE60; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f9f9f9; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>欢迎加入！</h1>
        </div>
        <div class="content">
            <p>您好，{username}！</p>
            <p>欢迎加入我们的平台！您的账户已成功验证并激活。</p>
            <p>现在您可以开始使用我们的服务了。</p>
            <p>如有任何问题，请随时联系我们的支持团队。</p>
            <p>祝您使用愉快！</p>
        </div>
        <div class="footer">
            <p>此邮件由系统自动发送，请勿直接回复。</p>
        </div>
    </div>
</body>
</html>
"""
