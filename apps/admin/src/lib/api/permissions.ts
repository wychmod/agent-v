/**
 * 权限管理 API
 * 
 * 提供权限 CRUD 接口
 */

import apiClient from './client';
import type {
  Permission,
  CreatePermissionRequest,
  UpdatePermissionRequest,
} from '@/types';

/** 获取所有权限 */
async function getPermissions(): Promise<Permission[]> {
  const response = await apiClient.get('/permissions');
  return response.data;
}

/** 创建权限 */
async function createPermission(data: CreatePermissionRequest): Promise<Permission> {
  const response = await apiClient.post('/permissions', data);
  return response.data;
}

/** 更新权限 */
async function updatePermission(permissionId: string, data: UpdatePermissionRequest): Promise<Permission> {
  const response = await apiClient.put(`/permissions/${permissionId}`, data);
  return response.data;
}

/** 删除权限 */
async function deletePermission(permissionId: string): Promise<void> {
  await apiClient.delete(`/permissions/${permissionId}`);
}

/** 权限 API 命名空间 */
export const permissionsApi = {
  getPermissions,
  createPermission,
  updatePermission,
  deletePermission,
};
