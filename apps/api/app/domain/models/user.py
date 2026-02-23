"""用户管理系统领域模型"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Permission(BaseModel):
    """权限领域模型"""

    id: int
    resource: str = Field(description="资源名称，如 user, role, system")
    action: str = Field(description="操作类型，如 create, read, update, delete")
    display_name: str = Field(description="权限显示名称")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    def get_full_name(self) -> str:
        """返回完整权限标识，格式: resource:action"""
        return f"{self.resource}:{self.action}"


class Role(BaseModel):
    """角色领域模型"""

    id: int
    name: str = Field(description="角色名称，如 admin, user, guest")
    display_name: str = Field(description="角色显示名称")
    description: str | None = Field(default=None, description="角色描述")
    created_at: datetime
    permissions: list[Permission] = Field(
        default_factory=list, description="角色拥有的权限列表"
    )

    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    """用户领域模型"""

    id: str = Field(description="用户唯一标识 (UUID)")
    email: EmailStr = Field(description="用户邮箱")
    username: str = Field(description="用户名")
    is_active: bool = Field(default=True, description="账户是否激活")
    is_verified: bool = Field(default=False, description="邮箱是否已验证")
    must_change_password: bool = Field(default=False, description="是否需要修改密码")
    last_login_at: datetime | None = Field(default=None, description="最后登录时间")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    roles: list[Role] = Field(default_factory=list, description="用户角色列表")

    model_config = ConfigDict(from_attributes=True)

    def has_role(self, role_name: str) -> bool:
        """检查用户是否拥有指定角色"""
        return any(role.name == role_name for role in self.roles)

    def has_permission(self, resource: str, action: str) -> bool:
        """检查用户是否拥有指定权限"""
        for role in self.roles:
            for permission in role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True
        return False

    def get_all_permissions(self) -> list[str]:
        """获取用户所有权限的完整标识列表"""
        permissions = set()
        for role in self.roles:
            for permission in role.permissions:
                permissions.add(permission.get_full_name())
        return list(permissions)

    def to_safe_dict(self) -> dict:
        """返回不包含敏感信息的字典"""
        return self.model_dump(exclude={"password_hash"})


class UserWithPassword(User):
    """包含密码哈希的用户模型，用于内部验证"""

    password_hash: str = Field(description="密码哈希值")


class AuditLog(BaseModel):
    """审计日志领域模型"""

    id: int | None = Field(default=None, description="日志ID")
    user_id: str | None = Field(default=None, description="操作用户ID")
    action: str = Field(description="操作类型，如 login, logout, create_user")
    resource: str = Field(description="操作资源，如 user, role")
    resource_id: str | None = Field(default=None, description="资源ID")
    ip_address: str | None = Field(default=None, description="请求IP地址")
    user_agent: str | None = Field(default=None, description="用户代理")
    status: str = Field(default="success", description="操作状态: success, failed")
    details: dict | None = Field(default=None, description="操作详情")
    created_at: datetime | None = Field(default=None, description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    """JWT Token 载荷"""

    user_id: str = Field(description="用户ID")
    session_id: str | None = Field(default=None, description="会话ID")
    exp: datetime = Field(description="过期时间")
    iat: datetime = Field(description="签发时间")
    token_type: str = Field(default="access", description="Token 类型: access, refresh")


class SessionData(BaseModel):
    """会话数据"""

    user_id: str = Field(description="用户ID")
    roles: list[str] = Field(default_factory=list, description="用户角色列表")
    permissions: list[str] = Field(default_factory=list, description="用户权限列表")
    ip_address: str | None = Field(default=None, description="登录IP")
    user_agent: str | None = Field(default=None, description="用户代理")
    login_at: datetime = Field(description="登录时间")
