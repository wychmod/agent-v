"""create user management tables

Revision ID: 001_user_management
Revises:
Create Date: 2026-02-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_user_management"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 创建用户表
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("is_verified", sa.Boolean(), default=False, nullable=False),
        sa.Column("must_change_password", sa.Boolean(), default=False, nullable=False),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_username", "users", ["username"])
    op.create_index("idx_users_is_active", "users", ["is_active"])
    op.create_index("idx_users_created_at", "users", ["created_at"])

    # 创建角色表
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 创建权限表
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("resource", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "resource", "action", name="uq_permissions_resource_action"
        ),
    )

    # 创建用户角色关联表
    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assigned_by", sa.String(36), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )
    op.create_index("idx_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("idx_user_roles_role_id", "user_roles", ["role_id"])

    # 创建角色权限关联表
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "permission_id",
            sa.Integer(),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "role_id", "permission_id", name="uq_role_permissions_role_permission"
        ),
    )
    op.create_index("idx_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index(
        "idx_role_permissions_permission_id", "role_permissions", ["permission_id"]
    )

    # 创建审计日志表
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="success"),
        sa.Column("details", mysql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "idx_audit_logs_user_id_created_at", "audit_logs", ["user_id", "created_at"]
    )
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("idx_audit_logs_status", "audit_logs", ["status"])

    # 插入预设角色
    op.execute(
        """
        INSERT INTO roles (name, display_name, description, created_at) VALUES
        ('admin', '系统管理员', '拥有系统所有权限', NOW()),
        ('user', '普通用户', '基础用户权限', NOW()),
        ('guest', '访客', '只读权限', NOW())
        """
    )

    # 插入预设权限
    op.execute(
        """
        INSERT INTO permissions (resource, action, display_name, created_at) VALUES
        ('user', 'create', '创建用户', NOW()),
        ('user', 'read', '查看用户', NOW()),
        ('user', 'update', '更新用户', NOW()),
        ('user', 'delete', '删除用户', NOW()),
        ('role', 'create', '创建角色', NOW()),
        ('role', 'read', '查看角色', NOW()),
        ('role', 'update', '更新角色', NOW()),
        ('role', 'delete', '删除角色', NOW()),
        ('permission', 'read', '查看权限', NOW()),
        ('permission', 'assign', '分配权限', NOW()),
        ('audit_log', 'read', '查看审计日志', NOW())
        """
    )

    # 为管理员角色分配所有权限
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id, created_at)
        SELECT 
            (SELECT id FROM roles WHERE name = 'admin'),
            id,
            NOW()
        FROM permissions
        """
    )

    # 为普通用户角色分配基础权限
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id, created_at)
        SELECT 
            (SELECT id FROM roles WHERE name = 'user'),
            id,
            NOW()
        FROM permissions
        WHERE (resource = 'user' AND action = 'read')
           OR (resource = 'role' AND action = 'read')
           OR (resource = 'permission' AND action = 'read')
        """
    )

    # 为访客角色分配只读权限
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id, created_at)
        SELECT 
            (SELECT id FROM roles WHERE name = 'guest'),
            id,
            NOW()
        FROM permissions
        WHERE action = 'read'
        """
    )

    # 创建默认管理员账户
    # 密码: Admin@123456 (bcrypt hash)
    op.execute(
        """
        INSERT INTO users (id, email, username, password_hash, is_active, is_verified, must_change_password, created_at, updated_at)
        VALUES (
            'admin-uuid-0001-0001-000000000001',
            'admin@example.com',
            'admin',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYf9X4BK5mZO',
            TRUE,
            TRUE,
            TRUE,
            NOW(),
            NOW()
        )
        """
    )

    # 为管理员分配 admin 角色
    op.execute(
        """
        INSERT INTO user_roles (user_id, role_id, assigned_at)
        VALUES (
            'admin-uuid-0001-0001-000000000001',
            (SELECT id FROM roles WHERE name = 'admin'),
            NOW()
        )
        """
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
