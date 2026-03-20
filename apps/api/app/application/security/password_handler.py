"""密码处理器模块

本模块提供密码相关的安全处理功能，包括密码哈希、验证和强度校验。

主要功能:
- 密码哈希：使用bcrypt算法对密码进行安全哈希
- 密码验证：验证明文密码与哈希值是否匹配
- 强度校验：检查密码是否符合安全策略要求

安全说明:
- 使用bcrypt算法，自带盐值，防止彩虹表攻击
- 默认使用12轮哈希，平衡安全性和性能
- 密码策略可通过配置文件调整
"""

import re

import bcrypt

from app.application.errors.exceptions import ValidationError
from core.config import Settings, get_settings


class PasswordHandler:
    """密码处理器

    负责密码的哈希、验证和强度校验工作。
    使用bcrypt算法确保密码存储的安全性。

    Attributes:
        BCRYPT_ROUNDS: bcrypt哈希轮数，值越大越安全但性能开销越大
        _settings: 应用配置实例，包含密码策略配置
    """

    BCRYPT_ROUNDS = 12  # bcrypt哈希轮数

    def __init__(self, settings: Settings | None = None) -> None:
        """初始化密码处理器

        Args:
            settings: 可选的配置实例，为None时使用全局配置
        """
        self._settings = settings or get_settings()

    @property
    def min_length(self) -> int:
        """获取密码最小长度要求"""
        return self._settings.password_min_length

    def hash_password(self, password: str) -> str:
        """对密码进行哈希处理

        流程:
        1. 将密码转换为UTF-8字节
        2. 生成随机盐值
        3. 使用bcrypt算法进行哈希

        Args:
            password: 明文密码

        Returns:
            哈希后的密码字符串
        """
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=self.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码是否正确

        Args:
            plain_password: 用户输入的明文密码
            hashed_password: 数据库中存储的哈希密码

        Returns:
            True表示密码匹配，False表示不匹配或验证失败
        """
        try:
            password_bytes = plain_password.encode("utf-8")
            hashed_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            # 捕获所有异常，防止通过异常信息泄露敏感信息
            return False

    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        """验证密码强度

        检查密码是否符合安全策略要求:
        - 长度不少于最小长度（可配置）
        - 必须包含小写字母
        - 必须包含大写字母
        - 必须包含数字
        - 必须包含特殊字符

        Args:
            password: 待验证的密码

        Returns:
            元组 (是否通过验证, 错误消息列表)
        """
        errors = []

        # 检查密码长度
        if len(password) < self.min_length:
            errors.append(f"密码长度至少为 {self.min_length} 个字符")

        # 检查是否包含小写字母
        if not re.search(r"[a-z]", password):
            errors.append("密码必须包含小写字母")

        # 检查是否包含大写字母
        if not re.search(r"[A-Z]", password):
            errors.append("密码必须包含大写字母")

        # 检查是否包含数字
        if not re.search(r"\d", password):
            errors.append("密码必须包含数字")

        # 检查是否包含特殊字符
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("密码必须包含特殊字符")

        return len(errors) == 0, errors

    def validate_password_or_raise(self, password: str) -> None:
        """验证密码强度，不通过则抛出异常

        Args:
            password: 待验证的密码

        Raises:
            ValidationError: 密码不符合强度要求时抛出，包含具体错误信息
        """
        is_valid, errors = self.validate_password_strength(password)
        if not is_valid:
            raise ValidationError(
                field="password",
                reason="; ".join(errors),
            )
