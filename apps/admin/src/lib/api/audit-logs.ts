/**
 * 审计日志 API
 * 
 * 提供审计日志查询接口
 */

import apiClient from './client';
import type { AuditLog, AuditLogQueryParams, AuditLogListResponse } from '@/types';

/** 获取审计日志列表 */
async function getAuditLogs(params?: AuditLogQueryParams): Promise<AuditLogListResponse> {
  const response = await apiClient.get('/audit-logs', { params });
  return response.data.data;
}

/** 获取单条审计日志详情 */
async function getAuditLog(logId: string): Promise<AuditLog> {
  const response = await apiClient.get(`/audit-logs/${logId}`);
  return response.data.data;
}

/** 审计日志 API 命名空间 */
export const auditLogsApi = {
  getAuditLogs,
  getAuditLog,
};
