"""密码处理器测试

测试密码哈希、验证和强度校验：
- 密码哈希生成
- 密码验证
- 密码强度校验规则
"""

from unittest.mock import MagicMock

import pytest

from app.application.errors.exceptions import ValidationError
from app.application.security.password_handler import PasswordHandler


class TestPasswordHandler:
    """密码处理器测试"""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """创建 mock 设置"""
        settings = MagicMock()
        settings.password_min_length = 8
        return settings

    @pytest.fixture
    def handler(self, mock_settings: MagicMock) -> PasswordHandler:
        """创建密码处理器实例"""
        return PasswordHandler(settings=mock_settings)

    def test_hash_password(self, handler: PasswordHandler) -> None:
        """测试密码哈希生成"""
        password = "TestPassword123!"
        hashed = handler.hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt 前缀

    def test_hash_password_different_each_time(self, handler: PasswordHandler) -> None:
        """测试同一密码每次哈希结果不同（因为盐值不同）"""
        password = "TestPassword123!"
        hash1 = handler.hash_password(password)
        hash2 = handler.hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self, handler: PasswordHandler) -> None:
        """测试正确密码验证"""
        password = "TestPassword123!"
        hashed = handler.hash_password(password)

        assert handler.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, handler: PasswordHandler) -> None:
        """测试错误密码验证"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = handler.hash_password(password)

        assert handler.verify_password(wrong_password, hashed) is False

    def test_verify_password_invalid_hash(self, handler: PasswordHandler) -> None:
        """测试无效哈希值"""
        assert handler.verify_password("password", "invalid_hash") is False

    def test_verify_password_empty_inputs(self, handler: PasswordHandler) -> None:
        """测试空输入"""
        assert handler.verify_password("", "") is False

    def test_validate_password_strength_valid(self, handler: PasswordHandler) -> None:
        """测试有效密码强度"""
        password = "ValidPass123!"
        is_valid, errors = handler.validate_password_strength(password)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_password_strength_too_short(
        self, handler: PasswordHandler
    ) -> None:
        """测试密码过短"""
        password = "Ab1!"
        is_valid, errors = handler.validate_password_strength(password)

        assert is_valid is False
        assert any("长度" in error for error in errors)

    def test_validate_password_strength_no_lowercase(
        self, handler: PasswordHandler
    ) -> None:
        """测试缺少小写字母"""
        password = "UPPERCASE123!"
        is_valid, errors = handler.validate_password_strength(password)

        assert is_valid is False
        assert any("小写字母" in error for error in errors)

    def test_validate_password_strength_no_uppercase(
        self, handler: PasswordHandler
    ) -> None:
        """测试缺少大写字母"""
        password = "lowercase123!"
        is_valid, errors = handler.validate_password_strength(password)

        assert is_valid is False
        assert any("大写字母" in error for error in errors)

    def test_validate_password_strength_no_digit(
        self, handler: PasswordHandler
    ) -> None:
        """测试缺少数字"""
        password = "NoDigitsHere!"
        is_valid, errors = handler.validate_password_strength(password)

        assert is_valid is False
        assert any("数字" in error for error in errors)

    def test_validate_password_strength_no_special(
        self, handler: PasswordHandler
    ) -> None:
        """测试缺少特殊字符"""
        password = "NoSpecial123"
        is_valid, errors = handler.validate_password_strength(password)

        assert is_valid is False
        assert any("特殊字符" in error for error in errors)

    def test_validate_password_strength_multiple_errors(
        self, handler: PasswordHandler
    ) -> None:
        """测试多个错误"""
        password = "abc"  # 太短、无大写、无数字、无特殊字符
        is_valid, errors = handler.validate_password_strength(password)

        assert is_valid is False
        assert len(errors) >= 3

    def test_validate_password_or_raise_valid(self, handler: PasswordHandler) -> None:
        """测试有效密码不抛异常"""
        password = "ValidPass123!"
        handler.validate_password_or_raise(password)  # 不应抛出异常

    def test_validate_password_or_raise_invalid(self, handler: PasswordHandler) -> None:
        """测试无效密码抛出 ValidationError"""
        password = "weak"

        with pytest.raises(ValidationError) as exc_info:
            handler.validate_password_or_raise(password)

        assert exc_info.value.status_code == 422

    def test_min_length_property(self, handler: PasswordHandler) -> None:
        """测试最小长度属性"""
        assert handler.min_length == 8

    def test_unicode_password(self, handler: PasswordHandler) -> None:
        """测试 Unicode 密码"""
        password = "密码Test123!"
        hashed = handler.hash_password(password)

        assert handler.verify_password(password, hashed) is True

    def test_very_long_password(self, handler: PasswordHandler) -> None:
        """测试超长密码（bcrypt 限制 72 字节）"""
        # bcrypt 限制密码最长为 72 字节
        password = "Aa1!" + "x" * 66  # 70 字节，安全范围内
        hashed = handler.hash_password(password)

        assert handler.verify_password(password, hashed) is True
