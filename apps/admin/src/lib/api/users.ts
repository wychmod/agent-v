/**
 * 用户管理 API
 * 
 * 提供用户 CRUD、角色分配等用户管理接口
 */

import apiClient from './client';
import type {
  UserInfo,
  CreateUserRequest,
  UpdateUserRequest,
} from '@/types';

/** 用户列表查询参数 */
export interface GetUsersParams {
  page?: number;
  page_size?: number;
  search?: string;
}

/** 用户列表响应 */
export interface UsersListResponse {
  items: UserInfo[];
  total: number;
  page: number;
  page_size: number;
}

/** 获取用户列表 */
async function getUsers(params?: GetUsersParams): Promise<UsersListResponse> {
  const response = await apiClient.get('/users', { params });
  return response.data;
}

/** 获取用户详情 */
async function getUser(userId: string): Promise<UserInfo> {
  const response = await apiClient.get(`/users/${userId}`);
  return response.data;
}

/** 获取当前用户信息 */
async function getCurrentUser(): Promise<UserInfo> {
  const response = await apiClient.get('/users/me');
  return response.data;
}

/** 创建用户（管理员） */
async function createUser(data: CreateUserRequest): Promise<UserInfo> {
  const response = await apiClient.post('/users', data);
  return response.data;
}

/** 更新用户（管理员） */
async function updateUser(userId: string, data: UpdateUserRequest): Promise<UserInfo> {
  const response = await apiClient.put(`/users/${userId}`, data);
  return response.data;
}

/** 删除用户 */
async function deleteUser(userId: string): Promise<void> {
  await apiClient.delete(`/users/${userId}`);
}

/** 为用户分配角色 */
async function assignRole(userId: string, roleId: string): Promise<void> {
  await apiClient.post(`/users/${userId}/roles/${roleId}`);
}

/** 移除用户角色 */
async function removeRole(userId: string, roleId: string): Promise<void> {
  await apiClient.delete(`/users/${userId}/roles/${roleId}`);
}

/** 修改当前用户密码 */
async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  await apiClient.put('/users/me/password', {
    old_password: oldPassword,
    new_password: newPassword,
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
