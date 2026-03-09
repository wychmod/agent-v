/**
 * 系统状态 API
 * 
 * 提供系统健康检查接口
 */

import apiClient from './client';
import type { HealthStatus } from '@/types';

/** 获取系统健康状态 */
async function getStatus(): Promise<HealthStatus[]> {
  const response = await apiClient.get('/status');
  return response.data.data;
}

/** 状态 API 命名空间 */
export const statusApi = {
  getStatus,
};
