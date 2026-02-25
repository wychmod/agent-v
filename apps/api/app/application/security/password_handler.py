"""密码处理器"""

import re

import bcrypt

from app.application.errors.exceptions import ValidationError
from core.config import Settings, get_settings


class PasswordHandler:
    """密码处理器"""

    BCRYPT_ROUNDS = 12

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def min_length(self) -> int:
        return self._settings.password_min_length

    def hash_password(self, password: str) -> str:
        """对密码进行哈希处理"""
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=self.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码是否正确"""
        try:
            password_bytes = plain_password.encode("utf-8")
            hashed_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False

    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        """验证密码强度

        Returns:
            (是否通过验证, 错误消息列表)
        """
        errors = []

        if len(password) < self.min_length:
            errors.append(f"密码长度至少为 {self.min_length} 个字符")

        if not re.search(r"[a-z]", password):
            errors.append("密码必须包含小写字母")

        if not re.search(r"[A-Z]", password):
            errors.append("密码必须包含大写字母")

        if not re.search(r"\d", password):
            errors.append("密码必须包含数字")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("密码必须包含特殊字符")

        return len(errors) == 0, errors

    def validate_password_or_raise(self, password: str) -> None:
        """验证密码强度，不通过则抛出异常"""
        is_valid, errors = self.validate_password_strength(password)
        if not is_valid:
            raise ValidationError(
                field="password",
                reason="; ".join(errors),
            )
