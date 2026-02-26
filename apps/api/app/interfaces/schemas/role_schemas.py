"""角色和权限管理相关 Pydantic Schema

本模块定义角色和权限管理 API 的请求和响应数据模型。
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CreateRoleSchema(BaseModel):
    """创建角色请求"""

    name: str = Field(
        min_length=3,
        max_length=50,
        description="角色名称，只允许小写字母、数字和下划线",
    )
    display_name: str = Field(
        min_length=1,
        max_length=100,
        description="角色显示名称",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="角色描述",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证角色名称格式"""
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError("角色名称只允许小写字母、数字和下划线，且必须以字母开头")
        return v


class UpdateRoleSchema(BaseModel):
    """更新角色请求"""

    display_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="角色显示名称",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="角色描述",
    )


class RoleDetailResponse(BaseModel):
    """角色详情响应（包含权限信息）"""

    id: int = Field(description="角色ID")
    name: str = Field(description="角色名称")
    display_name: str = Field(description="显示名称")
    description: str | None = Field(default=None, description="角色描述")
    created_at: datetime = Field(description="创建时间")
    permission_count: int = Field(default=0, description="权限数量")
    user_count: int = Field(default=0, description="用户数量")

    model_config = ConfigDict(from_attributes=True)


class CreatePermissionSchema(BaseModel):
    """创建权限请求"""

    resource: str = Field(
        min_length=2,
        max_length=50,
        description="资源名称，如 user, role, system",
    )
    action: str = Field(
        min_length=2,
        max_length=50,
        description="操作类型，如 create, read, update, delete",
    )
    display_name: str = Field(
        min_length=1,
        max_length=100,
        description="权限显示名称",
    )

    @field_validator("resource", "action")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        """验证资源和操作标识符格式"""
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError("只允许小写字母、数字和下划线，且必须以字母开头")
        return v


class UpdatePermissionSchema(BaseModel):
    """更新权限请求"""

    display_name: str = Field(
        min_length=1,
        max_length=100,
        description="权限显示名称",
    )


class AdminCreateUserSchema(BaseModel):
    """管理员创建用户请求"""

    email: EmailStr = Field(description="用户邮箱")
    username: str = Field(
        min_length=3,
        max_length=20,
        description="用户名，只允许字母、数字和下划线",
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="用户密码",
    )
    is_active: bool = Field(
        default=True,
        description="是否激活账户",
    )
    must_change_password: bool = Field(
        default=False,
        description="是否强制用户首次登录时修改密码",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", v):
            raise ValueError("用户名只允许字母、数字和下划线，且必须以字母开头")
        return v


class AdminUpdateUserSchema(BaseModel):
    """管理员更新用户请求"""

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=20,
        description="用户名",
    )
    email: EmailStr | None = Field(
        default=None,
        description="用户邮箱",
    )
    is_active: bool | None = Field(
        default=None,
        description="是否激活账户",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        """验证用户名格式"""
        if v is not None and not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", v):
            raise ValueError("用户名只允许字母、数字和下划线，且必须以字母开头")
        return v
