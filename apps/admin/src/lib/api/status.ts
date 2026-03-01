/**
 * 系统状态 API
 * 
 * 提供系统健康检查接口
 */

import apiClient from './client';
import type { SystemStatus } from '@/types';

/** 获取系统健康状态 */
async function getStatus(): Promise<SystemStatus> {
  const response = await apiClient.get('/status');
  return response.data;
}

/** 状态 API 命名空间 */
export const statusApi = {
  getStatus,
};
