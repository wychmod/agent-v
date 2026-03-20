"""用户管理相关 Pydantic Schema 模块

本模块定义用户管理 API 的请求和响应数据模型。

主要数据模型:
请求模型:
- UpdateProfileSchema: 更新用户资料请求
- AssignRoleSchema: 分配角色请求
- AssignPermissionSchema: 分配权限请求

响应模型:
- RoleResponse: 角色信息响应
- PermissionResponse: 权限信息响应
- UserDetailResponse: 用户详情响应
- UserListResponse: 用户列表响应
- AuditLogResponse: 审计日志响应
- AuditLogListResponse: 审计日志列表响应
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UpdateProfileSchema(BaseModel):
    """更新用户资料请求模型"""

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=20,
        description="用户名",
    )


class AssignRoleSchema(BaseModel):
    """分配角色请求模型"""

    role_name: str = Field(description="角色名称")


class AssignPermissionSchema(BaseModel):
    """分配权限请求模型"""

    permission_id: int = Field(description="权限ID")


class RoleResponse(BaseModel):
    """角色信息响应模型"""

    id: int = Field(description="角色ID")
    name: str = Field(description="角色名称")
    display_name: str = Field(description="显示名称")
    description: str | None = Field(default=None, description="角色描述")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class PermissionResponse(BaseModel):
    """权限信息响应模型"""

    id: int = Field(description="权限ID")
    resource: str = Field(description="资源名称")
    action: str = Field(description="操作类型")
    display_name: str = Field(description="显示名称")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(BaseModel):
    """用户详情响应模型

    包含用户的完整信息，包括关联的角色列表。
    """

    id: str = Field(description="用户ID")
    email: str = Field(description="邮箱")
    username: str = Field(description="用户名")
    is_active: bool = Field(description="是否激活")
    is_verified: bool = Field(description="邮箱是否验证")
    must_change_password: bool = Field(default=False, description="是否需要修改密码")
    last_login_at: datetime | None = Field(default=None, description="最后登录时间")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    roles: list[RoleResponse] = Field(default_factory=list, description="角色列表")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_user(cls, user) -> "UserDetailResponse":
        """从用户领域模型创建响应对象

        Args:
            user: 用户领域模型对象

        Returns:
            UserDetailResponse: 用户详情响应对象
        """
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            must_change_password=user.must_change_password,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=[
                RoleResponse(
                    id=role.id,
                    name=role.name,
                    display_name=role.display_name,
                    description=role.description,
                    created_at=role.created_at,
                )
                for role in user.roles
            ],
        )


class UserListResponse(BaseModel):
    """用户列表响应模型（分页）"""

    items: list[UserDetailResponse] = Field(description="用户列表")
    total: int = Field(description="总数")
    skip: int = Field(description="跳过数量")
    limit: int = Field(description="每页数量")


class AuditLogResponse(BaseModel):
    """审计日志响应模型"""

    id: int | None = Field(default=None, description="日志ID")
    user_id: str | None = Field(default=None, description="用户ID")
    action: str = Field(description="操作类型")
    resource: str = Field(description="资源类型")
    resource_id: str | None = Field(default=None, description="资源ID")
    ip_address: str | None = Field(default=None, description="IP地址")
    user_agent: str | None = Field(default=None, description="用户代理")
    status: str = Field(description="状态")
    details: dict | None = Field(default=None, description="详情")
    created_at: datetime | None = Field(default=None, description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """审计日志列表响应模型（分页）"""

    items: list[AuditLogResponse] = Field(description="日志列表")
    total: int = Field(description="总数")
    skip: int = Field(description="跳过数量")
    limit: int = Field(description="每页数量")
