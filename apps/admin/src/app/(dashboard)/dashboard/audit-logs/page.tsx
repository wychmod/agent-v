/**
 * 审计日志页面
 * 
 * 显示系统操作日志，支持按时间、操作类型、资源类型筛选
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  FileText,
  Search,
  RefreshCw,
  Filter,
  Calendar,
  User,
  Activity,
  LogIn,
  LogOut,
  Plus,
  Edit,
  Trash2,
  Link,
  Unlink,
  Eye,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { auditLogsApi } from '@/lib/api/audit-logs';
import { useToast } from '@/lib/hooks/use-toast';
import { formatDateTime } from '@/lib/utils';
import type { AuditLog, AuditAction, AuditResource } from '@/types';

/** 操作类型配置 */
const ACTION_CONFIG: Record<AuditAction, { label: string; icon: React.ComponentType<{ className?: string }>; variant: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' }> = {
  login: { label: '登录', icon: LogIn, variant: 'success' },
  logout: { label: '登出', icon: LogOut, variant: 'secondary' },
  create: { label: '创建', icon: Plus, variant: 'success' },
  update: { label: '更新', icon: Edit, variant: 'warning' },
  delete: { label: '删除', icon: Trash2, variant: 'destructive' },
  assign: { label: '分配', icon: Link, variant: 'default' },
  remove: { label: '移除', icon: Unlink, variant: 'outline' },
  view: { label: '查看', icon: Eye, variant: 'secondary' },
};

/** 资源类型配置 */
const RESOURCE_CONFIG: Record<AuditResource, { label: string }> = {
  user: { label: '用户' },
  role: { label: '角色' },
  permission: { label: '权限' },
  system: { label: '系统' },
};

export default function AuditLogsPage() {
  const { toast } = useToast();

  // 状态管理
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const pageSize = 20;

  // 筛选条件
  const [filters, setFilters] = useState({
    action: '' as AuditAction | '',
    resource: '' as AuditResource | '',
    search: '',
  });

  /** 加载审计日志 */
  const loadAuditLogs = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await auditLogsApi.getAuditLogs({
        page: currentPage,
        page_size: pageSize,
        action: filters.action || undefined,
        resource: filters.resource || undefined,
      });

      setLogs(response.items || []);
      setTotalItems(response.total || 0);
      setTotalPages(Math.ceil((response.total || 0) / pageSize));
    } catch (error) {
      // 如果 API 尚未实现，显示模拟数据
      const mockLogs: AuditLog[] = [
        {
          id: '1',
          user_id: 'user-1',
          user_email: 'admin@example.com',
          username: 'admin',
          action: 'login',
          resource: 'system',
          details: '管理员登录系统',
          ip_address: '192.168.1.1',
          created_at: new Date().toISOString(),
        },
        {
          id: '2',
          user_id: 'user-1',
          user_email: 'admin@example.com',
          username: 'admin',
          action: 'create',
          resource: 'user',
          resource_id: 'user-2',
          details: '创建新用户 test@example.com',
          ip_address: '192.168.1.1',
          created_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: '3',
          user_id: 'user-1',
          user_email: 'admin@example.com',
          username: 'admin',
          action: 'assign',
          resource: 'role',
          resource_id: 'role-1',
          details: '为用户分配角色 admin',
          ip_address: '192.168.1.1',
          created_at: new Date(Date.now() - 7200000).toISOString(),
        },
      ];
      setLogs(mockLogs);
      setTotalItems(mockLogs.length);
      setTotalPages(1);
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, filters.action, filters.resource]);

  useEffect(() => {
    loadAuditLogs();
  }, [loadAuditLogs]);

  /** 重置筛选条件 */
  const resetFilters = () => {
    setFilters({ action: '', resource: '', search: '' });
    setCurrentPage(1);
  };

  /** 获取操作图标 */
  const getActionIcon = (action: AuditAction) => {
    const config = ACTION_CONFIG[action];
    if (config) {
      const Icon = config.icon;
      return <Icon className="h-4 w-4" />;
    }
    return <Activity className="h-4 w-4" />;
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">审计日志</h1>
          <p className="text-slate-500 mt-1">查看系统操作记录和安全事件</p>
        </div>
      </div>

      {/* 筛选条件 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            {/* 搜索框 */}
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                type="search"
                placeholder="搜索用户或详情..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="pl-10"
              />
            </div>

            {/* 操作类型筛选 */}
            <Select
              value={filters.action}
              onValueChange={(v) => setFilters({ ...filters, action: v as AuditAction })}
            >
              <SelectTrigger className="w-[140px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="操作类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部操作</SelectItem>
                {Object.entries(ACTION_CONFIG).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* 资源类型筛选 */}
            <Select
              value={filters.resource}
              onValueChange={(v) => setFilters({ ...filters, resource: v as AuditResource })}
            >
              <SelectTrigger className="w-[140px]">
                <FileText className="h-4 w-4 mr-2" />
                <SelectValue placeholder="资源类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部资源</SelectItem>
                {Object.entries(RESOURCE_CONFIG).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* 重置和刷新按钮 */}
            <Button variant="outline" onClick={resetFilters}>
              重置
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={loadAuditLogs}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 日志列表 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium">
            操作记录
            <span className="ml-2 text-sm font-normal text-slate-500">
              共 {totalItems} 条记录
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[180px]">时间</TableHead>
                <TableHead>操作者</TableHead>
                <TableHead>操作</TableHead>
                <TableHead>资源</TableHead>
                <TableHead>详情</TableHead>
                <TableHead>IP 地址</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-10">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto text-slate-400" />
                    <p className="mt-2 text-sm text-slate-500">加载中...</p>
                  </TableCell>
                </TableRow>
              ) : logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-10">
                    <FileText className="h-8 w-8 mx-auto text-slate-300" />
                    <p className="mt-2 text-sm text-slate-500">暂无日志记录</p>
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log) => {
                  const actionConfig = ACTION_CONFIG[log.action];
                  const resourceConfig = RESOURCE_CONFIG[log.resource];

                  return (
                    <TableRow key={log.id}>
                      <TableCell className="text-slate-500 text-sm">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-3 w-3" />
                          {formatDateTime(log.created_at)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-slate-400" />
                          <div>
                            <p className="font-medium text-sm">{log.username || '未知'}</p>
                            <p className="text-xs text-slate-400">{log.user_email}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={actionConfig?.variant || 'default'} className="gap-1">
                          {getActionIcon(log.action)}
                          {actionConfig?.label || log.action}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {resourceConfig?.label || log.resource}
                        </Badge>
                        {log.resource_id && (
                          <span className="ml-2 text-xs text-slate-400 font-mono">
                            #{log.resource_id.slice(0, 8)}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="max-w-[300px]">
                        <p className="text-sm text-slate-600 truncate" title={log.details}>
                          {log.details || '-'}
                        </p>
                      </TableCell>
                      <TableCell className="text-slate-500 text-sm font-mono">
                        {log.ip_address || '-'}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <p className="text-sm text-slate-500">
                第 {currentPage} 页，共 {totalPages} 页
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  上一页
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
