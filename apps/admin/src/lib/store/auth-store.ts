/**
 * 认证状态管理 Store
 * 
 * 使用 Zustand 管理用户认证状态，包括 Token 和用户信息
 * 同时同步 cookie 以供中间件进行路由保护
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserInfo } from '@/types';

/** Cookie 操作辅助函数 */
const setCookie = (name: string, value: string, days: number = 7) => {
  if (typeof document === 'undefined') return;
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
};

const removeCookie = (name: string) => {
  if (typeof document === 'undefined') return;
  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
};

/** 认证状态接口 */
interface AuthState {
  /** 访问令牌 */
  accessToken: string | null;
  /** 刷新令牌 */
  refreshToken: string | null;
  /** 当前用户信息 */
  user: UserInfo | null;
  /** 是否已认证 */
  isAuthenticated: boolean;

  /** 设置认证信息（登录成功后调用） */
  setAuth: (accessToken: string, refreshToken: string, user: UserInfo) => void;
  /** 更新访问令牌（刷新令牌后调用） */
  setAccessToken: (accessToken: string) => void;
  /** 更新用户信息 */
  setUser: (user: UserInfo) => void;
  /** 清除认证信息（登出时调用） */
  clearAuth: () => void;
}

/** 认证状态 Store */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      setAuth: (accessToken, refreshToken, user) => {
        // 同步设置 cookie 供中间件使用
        setCookie('auth-token', accessToken);
        set({
          accessToken,
          refreshToken,
          user,
          isAuthenticated: true,
        });
      },

      setAccessToken: (accessToken) => {
        // 更新 cookie
        setCookie('auth-token', accessToken);
        set({
          accessToken,
        });
      },

      setUser: (user) =>
        set({
          user,
        }),

      clearAuth: () => {
        // 清除 cookie
        removeCookie('auth-token');
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: 'auth-storage', // localStorage key
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      // 跳过自动 hydration，避免 hydration 不匹配
      skipHydration: true,
      // rehydrate 完成后同步 cookie
      onRehydrateStorage: () => (state) => {
        if (state?.accessToken) {
          setCookie('auth-token', state.accessToken);
        }
      },
    }
  )
);

/** 获取认证状态（非 Hook 方式，用于 API 客户端） */
export const getAuthState = () => useAuthStore.getState();
