"""用户管理系统 ORM 模型定义模块

本模块定义用户管理系统的所有数据库模型，实现 RBAC（基于角色的访问控制）权限模型。

模型层级结构:
- UserModel: 用户基本信息
- RoleModel: 角色定义
- PermissionModel: 权限定义
- UserRoleModel: 用户-角色关联（多对多）
- RolePermissionModel: 角色-权限关联（多对多）
- AuditLogModel: 审计日志记录

表关系说明:
- 一个用户可以拥有多个角色
- 一个角色可以包含多个权限
- 用户通过角色间接获得权限
- 审计日志记录用户的所有关键操作

索引优化:
- 为常用查询字段建立了索引
- 复合索引优化关联查询性能
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base


def generate_uuid() -> str:
    """生成 UUID 字符串作为主键

    Returns:
        str: UUID4 格式的字符串
    """
    return str(uuid.uuid4())


class UserModel(Base):
    """用户表 ORM 模型

    存储用户账户的基本信息和状态。

    Attributes:
        id: 用户唯一标识（UUID）
        email: 邮箱地址（唯一）
        username: 用户名（唯一）
        password_hash: 密码哈希值
        is_active: 账户是否激活
        is_verified: 邮箱是否已验证
        must_change_password: 是否必须修改密码
        last_login_at: 最后登录时间
        created_at: 创建时间
        updated_at: 更新时间
        roles: 用户角色关联列表
        audit_logs: 用户审计日志列表
    """

    __tablename__ = "users"

    # 主键和基本信息
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # 账户状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # 时间戳
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ORM 关系映射
    roles: Mapped[list["UserRoleModel"]] = relationship(
        "UserRoleModel", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLogModel"]] = relationship(
        "AuditLogModel", back_populates="user"
    )

    # 表级配置：索引定义
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
        Index("idx_users_is_active", "is_active"),
        Index("idx_users_created_at", "created_at"),
    )

    def __str__(self) -> str:
        return f"{self.username} ({self.email})"


class RoleModel(Base):
    """角色表 ORM 模型

    定义系统中的角色，用于权限分组管理。

    Attributes:
        id: 角色 ID（自增主键）
        name: 角色标识名（唯一，如 admin、user）
        display_name: 角色显示名称
        description: 角色描述
        created_at: 创建时间
        users: 拥有此角色的用户关联列表
        permissions: 角色权限关联列表
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # ORM 关系映射
    users: Mapped[list["UserRoleModel"]] = relationship(
        "UserRoleModel", back_populates="role"
    )
    permissions: Mapped[list["RolePermissionModel"]] = relationship(
        "RolePermissionModel", back_populates="role", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        return self.display_name


class PermissionModel(Base):
    """权限表 ORM 模型

    定义系统中的细粒度权限，采用资源-操作模式。

    Attributes:
        id: 权限 ID（自增主键）
        resource: 资源标识（如 user、role）
        action: 操作标识（如 create、read、update、delete）
        display_name: 权限显示名称
        created_at: 创建时间
        roles: 包含此权限的角色关联列表

    Note:
        resource + action 组合唯一，如 user:create、role:delete
    """

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # ORM 关系映射
    roles: Mapped[list["RolePermissionModel"]] = relationship(
        "RolePermissionModel", back_populates="permission"
    )

    # 表级配置：资源和操作组合唯一约束
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
    )

    def __str__(self) -> str:
        return f"{self.resource}:{self.action}"


class UserRoleModel(Base):
    """用户-角色关联表 ORM 模型

    实现用户和角色的多对多关系。

    Attributes:
        id: 关联 ID（自增主键）
        user_id: 用户 ID（外键）
        role_id: 角色 ID（外键）
        assigned_by: 分配者用户 ID
        assigned_at: 分配时间
        user: 关联的用户对象
        role: 关联的角色对象
    """

    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    assigned_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # ORM 关系映射
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="roles")
    role: Mapped["RoleModel"] = relationship("RoleModel", back_populates="users")

    # 表级配置：唯一约束和索引
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        Index("idx_user_roles_user_id", "user_id"),
        Index("idx_user_roles_role_id", "role_id"),
    )

    def __str__(self) -> str:
        return f"用户{self.user_id} - 角色{self.role_id}"


class RolePermissionModel(Base):
    """角色-权限关联表 ORM 模型

    实现角色和权限的多对多关系。

    Attributes:
        id: 关联 ID（自增主键）
        role_id: 角色 ID（外键）
        permission_id: 权限 ID（外键）
        created_at: 创建时间
        role: 关联的角色对象
        permission: 关联的权限对象
    """

    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # ORM 关系映射
    role: Mapped["RoleModel"] = relationship("RoleModel", back_populates="permissions")
    permission: Mapped["PermissionModel"] = relationship(
        "PermissionModel", back_populates="roles"
    )

    # 表级配置：唯一约束和索引
    __table_args__ = (
        UniqueConstraint(
            "role_id", "permission_id", name="uq_role_permissions_role_permission"
        ),
        Index("idx_role_permissions_role_id", "role_id"),
        Index("idx_role_permissions_permission_id", "permission_id"),
    )

    def __str__(self) -> str:
        return f"角色{self.role_id} - 权限{self.permission_id}"


class AuditLogModel(Base):
    """审计日志表 ORM 模型

    记录用户的关键操作，用于安全审计和问题追踪。

    Attributes:
        id: 日志 ID（自增主键）
        user_id: 操作用户 ID（外键，可为空表示系统操作）
        action: 操作类型（如 login、create、update、delete）
        resource: 操作资源类型
        resource_id: 操作资源 ID
        ip_address: 客户端 IP 地址
        user_agent: 客户端 User-Agent
        status: 操作状态（success/failure）
        details: 操作详情（JSON 格式）
        created_at: 操作时间
        user: 关联的用户对象
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # ORM 关系映射
    user: Mapped["UserModel | None"] = relationship(
        "UserModel", back_populates="audit_logs"
    )

    # 表级配置：索引优化查询
    __table_args__ = (
        Index("idx_audit_logs_user_id_created_at", "user_id", "created_at"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_status", "status"),
    )

    def __str__(self) -> str:
        return f"{self.action} on {self.resource} ({self.created_at})"
