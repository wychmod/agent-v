"""认证相关 Pydantic Schema 模块

本模块定义认证 API 的请求和响应数据模型。

主要数据模型:
- UserRegisterSchema: 用户注册请求
- LoginSchema: 用户登录请求
- LogoutSchema: 用户登出请求
- RefreshTokenSchema: Token 刷新请求
- VerifyEmailSchema: 邮箱验证请求
- ResetPasswordRequestSchema: 密码重置请求
- ResetPasswordSchema: 执行密码重置请求
- ChangePasswordSchema: 修改密码请求
- TokenResponse: Token 响应
- LoginResponse: 登录响应（含用户信息）
- UserResponse: 用户基本信息响应

验证规则:
- 用户名: 3-20 字符，仅允许字母、数字和下划线
- 密码: 8-128 字符
- 邮箱: 标准邮箱格式
- 密码确认: 必须与密码一致
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegisterSchema(BaseModel):
    """用户注册请求模型

    包含注册所需的全部字段和验证规则。
    """

    email: EmailStr = Field(description="邮箱地址")
    username: str = Field(
        min_length=3,
        max_length=20,
        description="用户名（3-20个字符，只能包含字母、数字和下划线）",
    )
    password: str = Field(min_length=8, max_length=128, description="密码")
    password_confirm: str = Field(description="确认密码")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v

    @field_validator("password_confirm")
    @classmethod
    def validate_password_confirm(cls, v: str, info) -> str:
        """验证两次密码输入是否一致"""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("两次输入的密码不一致")
        return v


class LoginSchema(BaseModel):
    """用户登录请求模型"""

    email: EmailStr = Field(description="邮箱地址")
    password: str = Field(description="密码")


class TokenResponse(BaseModel):
    """Token 响应模型

    用于返回访问令牌和刷新令牌。
    """

    access_token: str = Field(description="访问令牌")
    refresh_token: str | None = Field(default=None, description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间（秒）")


class RefreshTokenSchema(BaseModel):
    """刷新令牌请求"""

    refresh_token: str = Field(description="刷新令牌")


class LogoutSchema(BaseModel):
    """登出请求"""

    refresh_token: str | None = Field(
        default=None, description="刷新令牌（如提供则一并失效）"
    )


class VerifyEmailSchema(BaseModel):
    """邮箱验证请求"""

    token: str = Field(description="验证令牌")


class ResetPasswordRequestSchema(BaseModel):
    """请求密码重置"""

    email: EmailStr = Field(description="邮箱地址")


class ResetPasswordSchema(BaseModel):
    """重置密码请求"""

    token: str = Field(description="重置令牌")
    new_password: str = Field(min_length=8, max_length=128, description="新密码")
    new_password_confirm: str = Field(description="确认新密码")

    @field_validator("new_password_confirm")
    @classmethod
    def validate_password_confirm(cls, v: str, info) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("两次输入的密码不一致")
        return v


class ChangePasswordSchema(BaseModel):
    """修改密码请求"""

    old_password: str = Field(description="原密码")
    new_password: str = Field(min_length=8, max_length=128, description="新密码")
    new_password_confirm: str = Field(description="确认新密码")

    @field_validator("new_password_confirm")
    @classmethod
    def validate_password_confirm(cls, v: str, info) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("两次输入的密码不一致")
        return v


class LoginResponse(BaseModel):
    """登录响应"""

    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间（秒）")
    user: "UserResponse" = Field(description="用户信息")


class UserResponse(BaseModel):
    """用户信息响应"""

    id: str = Field(description="用户ID")
    email: str = Field(description="邮箱")
    username: str = Field(description="用户名")
    is_active: bool = Field(description="是否激活")
    is_verified: bool = Field(description="邮箱是否验证")
    must_change_password: bool = Field(default=False, description="是否需要修改密码")
    roles: list[str] = Field(default_factory=list, description="角色列表")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_user(cls, user) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            must_change_password=user.must_change_password,
            roles=[role.name for role in user.roles],
            created_at=user.created_at,
        )


LoginResponse.model_rebuild()
