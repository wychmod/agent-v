/**
 * 认证 API
 * 
 * 提供登录、登出、刷新令牌等认证相关接口
 */

import apiClient from './client';
import type { LoginRequest, LoginResponse, TokenResponse } from '@/types';

/** 用户登录 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post('/auth/login', data);
  return response.data;
}

/** 用户登出 */
export async function logout(refreshToken?: string): Promise<void> {
  await apiClient.post('/auth/logout', { refresh_token: refreshToken });
}

/** 刷新令牌 */
export async function refreshToken(refresh_token: string): Promise<TokenResponse> {
  const response = await apiClient.post('/auth/refresh', { refresh_token });
  return response.data;
}
