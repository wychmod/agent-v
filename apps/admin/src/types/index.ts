/**
 * API 响应和数据类型定义
 * 
 * 定义与后端 API 交互的所有数据类型
 */

// ==================== API 通用类型 ====================

/** API 通用响应结构 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

// ==================== 认证相关类型 ====================

/** 登录请求 */
export interface LoginRequest {
  email: string;
  password: string;
}

/** 登录响应 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserInfo;
}

/** Token 响应 */
export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
}

// ==================== 用户相关类型 ====================

/** 用户基本信息（登录上下文，角色为名称字符串数组） */
export interface UserInfo {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  must_change_password: boolean;
  roles: string[];
  created_at: string;
}

/** 用户详情信息（管理上下文，角色为完整对象数组） */
export interface UserDetail {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  must_change_password: boolean;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
  roles: Role[];
}

/** 创建用户请求 */
export interface CreateUserRequest {
  email: string;
  username: string;
  password: string;
  is_active?: boolean;
  must_change_password?: boolean;
}

/** 管理员创建用户请求 */
export type AdminCreateUserRequest = CreateUserRequest;

/** 更新用户请求 */
export interface UpdateUserRequest {
  username?: string;
  email?: string;
  is_active?: boolean;
}

/** 管理员更新用户请求 */
export type AdminUpdateUserRequest = UpdateUserRequest;

/** 用户列表响应 */
export interface UsersListResponse {
  items: UserDetail[];
  total: number;
  skip: number;
  limit: number;
}

// ==================== 角色相关类型 ====================

/** 角色信息（匹配后端 RoleResponse） */
export interface Role {
  id: number;
  name: string;
  display_name: string;
  description?: string | null;
  created_at: string;
}

/** 角色详情（匹配后端 RoleDetailResponse，包含统计信息） */
export interface RoleDetail {
  id: number;
  name: string;
  display_name: string;
  description?: string | null;
  created_at: string;
  permission_count: number;
  user_count: number;
}

/** 创建角色请求 */
export interface CreateRoleRequest {
  name: string;
  display_name: string;
  description?: string;
}

/** 更新角色请求 */
export interface UpdateRoleRequest {
  display_name?: string;
  description?: string;
}

// ==================== 权限相关类型 ====================

/** 权限信息（匹配后端 PermissionResponse） */
export interface Permission {
  id: number;
  resource: string;
  action: string;
  display_name: string;
  created_at: string;
}

/** 创建权限请求 */
export interface CreatePermissionRequest {
  resource: string;
  action: string;
  display_name: string;
}

/** 更新权限请求 */
export interface UpdatePermissionRequest {
  display_name: string;
}

// ==================== 系统状态类型 ====================

/** 单个服务健康状态（匹配后端 HealthStatus） */
export interface HealthStatus {
  service: string;
  status: string;
  details: string;
}

// ==================== 审计日志类型 ====================

/** 审计日志操作类型 */
export type AuditAction = 
  | 'login'
  | 'logout'
  | 'create'
  | 'update'
  | 'delete'
  | 'assign'
  | 'remove'
  | 'view';

/** 审计日志资源类型 */
export type AuditResource = 
  | 'user'
  | 'role'
  | 'permission'
  | 'system';

/** 审计日志条目（匹配后端 AuditLogResponse） */
export interface AuditLog {
  id: number;
  user_id?: string;
  action: AuditAction;
  resource: AuditResource;
  resource_id?: string;
  ip_address?: string;
  user_agent?: string;
  status: string;
  details?: Record<string, unknown>;
  created_at: string;
}

/** 审计日志查询参数 */
export interface AuditLogQueryParams {
  skip?: number;
  limit?: number;
  action?: AuditAction;
  resource?: AuditResource;
  user_id?: string;
  start_date?: string;
  end_date?: string;
}

/** 审计日志列表响应 */
export interface AuditLogListResponse {
  items: AuditLog[];
  total: number;
  skip: number;
  limit: number;
}
