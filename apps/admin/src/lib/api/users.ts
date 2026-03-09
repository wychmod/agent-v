/**
 * 用户管理 API
 * 
 * 提供用户 CRUD、角色分配等用户管理接口
 */

import apiClient from './client';
import type {
  UserDetail,
  CreateUserRequest,
  UpdateUserRequest,
  UsersListResponse,
} from '@/types';

/** 用户列表查询参数 */
export interface GetUsersParams {
  skip?: number;
  limit?: number;
  is_active?: boolean;
}

/** 获取用户列表 */
async function getUsers(params?: GetUsersParams): Promise<UsersListResponse> {
  const response = await apiClient.get('/users', { params });
  return response.data.data;
}

/** 获取用户详情 */
async function getUser(userId: string): Promise<UserDetail> {
  const response = await apiClient.get(`/users/${userId}`);
  return response.data.data;
}

/** 获取当前用户信息 */
async function getCurrentUser(): Promise<UserDetail> {
  const response = await apiClient.get('/users/me');
  return response.data.data;
}

/** 创建用户（管理员） */
async function createUser(data: CreateUserRequest): Promise<UserDetail> {
  const response = await apiClient.post('/users', data);
  return response.data.data;
}

/** 更新用户（管理员） */
async function updateUser(userId: string, data: UpdateUserRequest): Promise<UserDetail> {
  const response = await apiClient.put(`/users/${userId}`, data);
  return response.data.data;
}

/** 删除用户 */
async function deleteUser(userId: string): Promise<void> {
  await apiClient.delete(`/users/${userId}`);
}

/** 为用户分配角色（通过角色名称） */
async function assignRole(userId: string, roleName: string): Promise<void> {
  await apiClient.put(`/users/${userId}/roles`, { role_name: roleName });
}

/** 移除用户角色（通过角色名称） */
async function removeRole(userId: string, roleName: string): Promise<void> {
  await apiClient.delete(`/users/${userId}/roles/${roleName}`);
}

/** 修改当前用户密码 */
async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  await apiClient.put('/users/me/password', {
    old_password: oldPassword,
    new_password: newPassword,
    new_password_confirm: newPassword,
  });
}

/** 用户 API 命名空间 */
export const usersApi = {
  getUsers,
  getUser,
  getCurrentUser,
  createUser,
  updateUser,
  deleteUser,
  assignRole,
  removeRole,
  changePassword,
};
