"""管理后台 ModelView 定义"""

from starlette_admin.contrib.sqla import ModelView

from app.infrastructure.models.user_models import (
    AuditLogModel,
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserModel,
    UserRoleModel,
)


class UserView(ModelView):
    """用户管理视图"""

    name = "用户"
    label = "用户管理"
    icon = "fa fa-users"

    exclude_fields_from_list = [
        UserModel.password_hash,
        UserModel.must_change_password,
        UserModel.updated_at,
        UserModel.roles,
        UserModel.audit_logs,
    ]
    exclude_fields_from_detail = [
        UserModel.password_hash,
    ]
    exclude_fields_from_create = [
        UserModel.id,
        UserModel.password_hash,
        UserModel.created_at,
        UserModel.updated_at,
        UserModel.last_login_at,
        UserModel.roles,
        UserModel.audit_logs,
    ]
    exclude_fields_from_edit = [
        UserModel.id,
        UserModel.password_hash,
        UserModel.created_at,
        UserModel.updated_at,
        UserModel.last_login_at,
        UserModel.roles,
        UserModel.audit_logs,
    ]
    searchable_fields = [UserModel.email, UserModel.username]
    sortable_fields = [
        UserModel.created_at,
        UserModel.email,
        UserModel.username,
        UserModel.is_active,
    ]
    fields_default_sort = [(UserModel.created_at, True)]
    page_size = 20
    page_size_options = [10, 20, 50, 100]
    export_types = []

    column_labels = {
        UserModel.id: "用户ID",
        UserModel.email: "邮箱",
        UserModel.username: "用户名",
        UserModel.password_hash: "密码哈希",
        UserModel.is_active: "激活状态",
        UserModel.is_verified: "已验证",
        UserModel.must_change_password: "需修改密码",
        UserModel.last_login_at: "最后登录",
        UserModel.created_at: "创建时间",
        UserModel.updated_at: "更新时间",
    }


class RoleView(ModelView):
    """角色管理视图"""

    name = "角色"
    label = "角色管理"
    icon = "fa fa-shield-halved"

    exclude_fields_from_list = [
        RoleModel.users,
        RoleModel.permissions,
    ]
    exclude_fields_from_create = [
        RoleModel.id,
        RoleModel.created_at,
        RoleModel.users,
        RoleModel.permissions,
    ]
    exclude_fields_from_edit = [
        RoleModel.id,
        RoleModel.created_at,
        RoleModel.users,
        RoleModel.permissions,
    ]
    searchable_fields = [RoleModel.name, RoleModel.display_name]
    sortable_fields = [RoleModel.name, RoleModel.display_name, RoleModel.created_at]
    fields_default_sort = [(RoleModel.created_at, True)]
    page_size = 20

    column_labels = {
        RoleModel.id: "角色ID",
        RoleModel.name: "角色名",
        RoleModel.display_name: "显示名称",
        RoleModel.description: "描述",
        RoleModel.created_at: "创建时间",
    }


class PermissionView(ModelView):
    """权限管理视图"""

    name = "权限"
    label = "权限管理"
    icon = "fa fa-key"

    exclude_fields_from_list = [
        PermissionModel.roles,
    ]
    exclude_fields_from_create = [
        PermissionModel.id,
        PermissionModel.created_at,
        PermissionModel.roles,
    ]
    exclude_fields_from_edit = [
        PermissionModel.id,
        PermissionModel.created_at,
        PermissionModel.roles,
    ]
    searchable_fields = [
        PermissionModel.resource,
        PermissionModel.action,
        PermissionModel.display_name,
    ]
    sortable_fields = [
        PermissionModel.resource,
        PermissionModel.action,
        PermissionModel.created_at,
    ]
    fields_default_sort = [(PermissionModel.created_at, True)]
    page_size = 20

    column_labels = {
        PermissionModel.id: "权限ID",
        PermissionModel.resource: "资源",
        PermissionModel.action: "动作",
        PermissionModel.display_name: "显示名称",
        PermissionModel.created_at: "创建时间",
    }


class UserRoleView(ModelView):
    """用户-角色关联视图"""

    name = "用户角色"
    label = "用户-角色关联"
    icon = "fa fa-user-tag"

    exclude_fields_from_create = [
        UserRoleModel.id,
        UserRoleModel.assigned_at,
    ]
    exclude_fields_from_edit = [
        UserRoleModel.id,
        UserRoleModel.assigned_at,
    ]
    sortable_fields = [UserRoleModel.assigned_at]
    fields_default_sort = [(UserRoleModel.assigned_at, True)]
    page_size = 20

    column_labels = {
        UserRoleModel.id: "关联ID",
        UserRoleModel.user: "用户",
        UserRoleModel.role: "角色",
        UserRoleModel.user_id: "用户ID",
        UserRoleModel.role_id: "角色ID",
        UserRoleModel.assigned_by: "分配人",
        UserRoleModel.assigned_at: "分配时间",
    }


class RolePermissionView(ModelView):
    """角色-权限关联视图"""

    name = "角色权限"
    label = "角色-权限关联"
    icon = "fa fa-lock"

    exclude_fields_from_create = [
        RolePermissionModel.id,
        RolePermissionModel.created_at,
    ]
    exclude_fields_from_edit = [
        RolePermissionModel.id,
        RolePermissionModel.created_at,
    ]
    sortable_fields = [RolePermissionModel.created_at]
    fields_default_sort = [(RolePermissionModel.created_at, True)]
    page_size = 20

    column_labels = {
        RolePermissionModel.id: "关联ID",
        RolePermissionModel.role: "角色",
        RolePermissionModel.permission: "权限",
        RolePermissionModel.role_id: "角色ID",
        RolePermissionModel.permission_id: "权限ID",
        RolePermissionModel.created_at: "创建时间",
    }


class AuditLogView(ModelView):
    """审计日志视图（只读）"""

    name = "审计日志"
    label = "审计日志"
    icon = "fa fa-clipboard-list"

    can_create = False
    can_edit = False
    can_delete = False

    exclude_fields_from_list = [
        AuditLogModel.user_agent,
        AuditLogModel.details,
    ]
    searchable_fields = [
        AuditLogModel.action,
        AuditLogModel.resource,
        AuditLogModel.status,
        AuditLogModel.ip_address,
    ]
    sortable_fields = [
        AuditLogModel.created_at,
        AuditLogModel.action,
        AuditLogModel.resource,
        AuditLogModel.status,
    ]
    fields_default_sort = [(AuditLogModel.created_at, True)]
    page_size = 50
    page_size_options = [25, 50, 100, 200]

    column_labels = {
        AuditLogModel.id: "日志ID",
        AuditLogModel.user: "用户",
        AuditLogModel.user_id: "用户ID",
        AuditLogModel.action: "操作",
        AuditLogModel.resource: "资源",
        AuditLogModel.resource_id: "资源ID",
        AuditLogModel.ip_address: "IP地址",
        AuditLogModel.user_agent: "用户代理",
        AuditLogModel.status: "状态",
        AuditLogModel.details: "详情",
        AuditLogModel.created_at: "创建时间",
    }
