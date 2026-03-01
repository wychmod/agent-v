/**
 * API 客户端配置
 * 
 * 基于 Axios 的 HTTP 客户端，包含认证拦截器和错误处理
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { getAuthState, useAuthStore } from '@/lib/store/auth-store';
import type { ApiResponse, TokenResponse } from '@/types';

/** 错误响应类型 */
interface ErrorResponse {
  message?: string;
  detail?: string;
}

/** API 基础 URL */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

/** 创建 Axios 实例 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/** 是否正在刷新 Token */
let isRefreshing = false;
/** 等待刷新 Token 的请求队列 */
let refreshSubscribers: ((token: string) => void)[] = [];

/** 添加请求到等待队列 */
const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb);
};

/** 执行等待队列中的请求 */
const onRefreshed = (token: string) => {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
};

/** 请求拦截器：添加认证 Token */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const { accessToken } = getAuthState();
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/** 响应拦截器：处理错误和 Token 刷新 */
apiClient.interceptors.response.use(
  (response) => {
    // 返回完整响应，让调用方处理
    return response;
  },
  async (error: AxiosError<ErrorResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // 处理 401 错误：尝试刷新 Token
    if (error.response?.status === 401 && !originalRequest._retry) {
      const { refreshToken, clearAuth } = useAuthStore.getState();

      // 如果没有刷新令牌，直接登出
      if (!refreshToken) {
        clearAuth();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      // 如果正在刷新，将请求加入队列
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(apiClient(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // 刷新 Token
        const response = await axios.post<ApiResponse<TokenResponse>>(
          `${API_BASE_URL}/auth/refresh`,
          { refresh_token: refreshToken },
          { headers: { 'Content-Type': 'application/json' } }
        );

        const newToken = response.data.data.access_token;
        useAuthStore.getState().setAccessToken(newToken);

        // 执行等待队列
        onRefreshed(newToken);

        // 重试原请求
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // 刷新失败，清除认证状态并跳转到登录页
        clearAuth();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // 提取错误信息
    const errorMessage =
      error.response?.data?.detail || error.response?.data?.message || error.message || '请求失败，请稍后重试';

    return Promise.reject(new Error(errorMessage));
  }
);

export default apiClient;
