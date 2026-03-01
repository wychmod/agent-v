/**
 * 角色管理 API
 * 
 * 提供角色 CRUD 和角色权限管理接口
 */

import apiClient from './client';
import type {
  Role,
  Permission,
  CreateRoleRequest,
  UpdateRoleRequest,
} from '@/types';

/** 获取所有角色 */
async function getRoles(): Promise<Role[]> {
  const response = await apiClient.get('/roles');
  return response.data;
}

/** 创建角色 */
async function createRole(data: CreateRoleRequest): Promise<Role> {
  const response = await apiClient.post('/roles', data);
  return response.data;
}

/** 更新角色 */
async function updateRole(roleId: string, data: UpdateRoleRequest): Promise<Role> {
  const response = await apiClient.put(`/roles/${roleId}`, data);
  return response.data;
}

/** 删除角色 */
async function deleteRole(roleId: string): Promise<void> {
  await apiClient.delete(`/roles/${roleId}`);
}

/** 获取角色权限 */
async function getRolePermissions(roleId: string): Promise<Permission[]> {
  const response = await apiClient.get(`/roles/${roleId}/permissions`);
  return response.data;
}

/** 为角色分配权限 */
async function assignPermission(roleId: string, permissionId: string): Promise<void> {
  await apiClient.post(`/roles/${roleId}/permissions/${permissionId}`);
}

/** 移除角色权限 */
async function removePermission(roleId: string, permissionId: string): Promise<void> {
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
