"""用户管理系统 ORM 模型定义"""

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
    return str(uuid.uuid4())


class UserModel(Base):
    """用户表"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系
    roles: Mapped[list["UserRoleModel"]] = relationship(
        "UserRoleModel", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLogModel"]] = relationship(
        "AuditLogModel", back_populates="user"
    )

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
        Index("idx_users_is_active", "is_active"),
        Index("idx_users_created_at", "created_at"),
    )

    def __str__(self) -> str:
        return f"{self.username} ({self.email})"


class RoleModel(Base):
    """角色表"""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # 关系
    users: Mapped[list["UserRoleModel"]] = relationship(
        "UserRoleModel", back_populates="role"
    )
    permissions: Mapped[list["RolePermissionModel"]] = relationship(
        "RolePermissionModel", back_populates="role", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        return self.display_name


class PermissionModel(Base):
    """权限表"""

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # 关系
    roles: Mapped[list["RolePermissionModel"]] = relationship(
        "RolePermissionModel", back_populates="permission"
    )

    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
    )

    def __str__(self) -> str:
        return f"{self.resource}:{self.action}"


class UserRoleModel(Base):
    """用户-角色关联表"""

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

    # 关系
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="roles")
    role: Mapped["RoleModel"] = relationship("RoleModel", back_populates="users")

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        Index("idx_user_roles_user_id", "user_id"),
        Index("idx_user_roles_role_id", "role_id"),
    )

    def __str__(self) -> str:
        return f"用户{self.user_id} - 角色{self.role_id}"


class RolePermissionModel(Base):
    """角色-权限关联表"""

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

    # 关系
    role: Mapped["RoleModel"] = relationship("RoleModel", back_populates="permissions")
    permission: Mapped["PermissionModel"] = relationship(
        "PermissionModel", back_populates="roles"
    )

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
    """审计日志表"""

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

    # 关系
    user: Mapped["UserModel | None"] = relationship(
        "UserModel", back_populates="audit_logs"
    )

    __table_args__ = (
        Index("idx_audit_logs_user_id_created_at", "user_id", "created_at"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_status", "status"),
    )

    def __str__(self) -> str:
        return f"{self.action} on {self.resource} ({self.created_at})"
