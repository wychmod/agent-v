/**
 * 角色管理 API
 * 
 * 提供角色 CRUD 和角色权限管理接口
 */

import apiClient from './client';
import type {
  Role,
  RoleDetail,
  Permission,
  CreateRoleRequest,
  UpdateRoleRequest,
} from '@/types';

/** 获取所有角色 */
async function getRoles(): Promise<Role[]> {
  const response = await apiClient.get('/roles');
  return response.data.data;
}

/** 创建角色 */
async function createRole(data: CreateRoleRequest): Promise<RoleDetail> {
  const response = await apiClient.post('/roles', data);
  return response.data.data;
}

/** 更新角色 */
async function updateRole(roleId: number, data: UpdateRoleRequest): Promise<RoleDetail> {
  const response = await apiClient.put(`/roles/${roleId}`, data);
  return response.data.data;
}

/** 删除角色 */
async function deleteRole(roleId: number): Promise<void> {
  await apiClient.delete(`/roles/${roleId}`);
}

/** 获取角色权限 */
async function getRolePermissions(roleId: number): Promise<Permission[]> {
  const response = await apiClient.get(`/roles/${roleId}/permissions`);
  return response.data.data;
}

/** 为角色分配权限（通过请求体传递 permission_id） */
async function assignPermission(roleId: number, permissionId: number): Promise<void> {
  await apiClient.post(`/roles/${roleId}/permissions`, { permission_id: permissionId });
}

/** 移除角色权限 */
async function removePermission(roleId: number, permissionId: number): Promise<void> {
  await apiClient.delete(`/roles/${roleId}/permissions/${permissionId}`);
}

/** 角色 API 命名空间 */
export const rolesApi = {
  getRoles,
  createRole,
  updateRole,
  deleteRole,
  getRolePermissions,
  assignPermission,
  removePermission,
};
