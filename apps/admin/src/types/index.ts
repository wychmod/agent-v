/**
 * API 响应和数据类型定义
 * 
 * 定义与后端 API 交互的所有数据类型
 */

// ==================== API 通用类型 ====================

/** API 通用响应结构 */
export interface ApiResponse<T = unknown> {
  code?: number;
  message?: string;
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

/** 角色简要信息（用于用户角色列表） */
export interface RoleBasic {
  id: string;
  name: string;
}

/** 用户基本信息 */
export interface UserInfo {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_verified?: boolean;
  must_change_password?: boolean;
  roles?: RoleBasic[];
  created_at: string;
  updated_at?: string;
}

/** 创建用户请求 */
export interface CreateUserRequest {
  email: string;
  username: string;
  password: string;
  is_active?: boolean;
}

/** 管理员创建用户请求（与 CreateUserRequest 相同，保留类型别名以保持兼容性） */
export type AdminCreateUserRequest = CreateUserRequest;

/** 更新用户请求 */
export interface UpdateUserRequest {
  username?: string;
  email?: string;
  password?: string;
  is_active?: boolean;
}

/** 管理员更新用户请求（与 UpdateUserRequest 相同，保留类型别名以保持兼容性） */
export type AdminUpdateUserRequest = UpdateUserRequest;

// ==================== 角色相关类型 ====================

/** 角色信息 */
export interface Role {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at?: string;
}

/** 创建角色请求 */
export interface CreateRoleRequest {
  name: string;
  description?: string;
}

/** 更新角色请求 */
export interface UpdateRoleRequest {
  name?: string;
  description?: string;
}

// ==================== 权限相关类型 ====================

/** 权限信息 */
export interface Permission {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at?: string;
}

/** 创建权限请求 */
export interface CreatePermissionRequest {
  name: string;
  description?: string;
}

/** 更新权限请求 */
export interface UpdatePermissionRequest {
  name?: string;
  description?: string;
}

// ==================== 系统状态类型 ====================

/** 系统状态响应 */
export interface SystemStatus {
  status: 'healthy' | 'unhealthy';
  database: 'connected' | 'disconnected';
  version?: string;
  message?: string;
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

/** 审计日志条目 */
export interface AuditLog {
  id: string;
  user_id: string;
  user_email?: string;
  username?: string;
  action: AuditAction;
  resource: AuditResource;
  resource_id?: string;
  details?: string;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

/** 审计日志查询参数 */
export interface AuditLogQueryParams {
  page?: number;
  page_size?: number;
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
  page: number;
  page_size: number;
}
