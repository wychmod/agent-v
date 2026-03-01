/**
 * Dashboard 首页
 * 
 * 显示系统概览统计信息和快捷操作入口
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
  Users,
  Shield,
  Key,
  Activity,
  Clock,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuthStore } from '@/lib/store/auth-store';
import { statusApi } from '@/lib/api/status';
import { usersApi } from '@/lib/api/users';
import { rolesApi } from '@/lib/api/roles';
import { permissionsApi } from '@/lib/api/permissions';
import { useToast } from '@/lib/hooks/use-toast';
import type { SystemStatus } from '@/types';

/** 统计卡片数据 */
interface StatCard {
  title: string;
  value: string | number;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [stats, setStats] = useState({
    users: 0,
    roles: 0,
    permissions: 0,
  });

  /** 加载统计数据 */
  const loadStats = useCallback(async () => {
    setIsLoading(true);
    try {
      // 并行加载所有数据
      const [usersRes, rolesRes, permissionsRes, statusRes] = await Promise.all([
        usersApi.getUsers({ page: 1, page_size: 1 }),
        rolesApi.getRoles(),
        permissionsApi.getPermissions(),
        statusApi.getStatus(),
      ]);

      setStats({
        users: usersRes.total || 0,
        roles: rolesRes.length || 0,
        permissions: permissionsRes.length || 0,
      });
      setSystemStatus(statusRes);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: '加载失败',
        description: '无法加载统计数据，请稍后重试',
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  /** 统计卡片配置 */
  const statCards: StatCard[] = [
    {
      title: '用户总数',
      value: stats.users,
      description: '系统注册用户',
      icon: Users,
      href: '/dashboard/users',
    },
    {
      title: '角色数量',
      value: stats.roles,
      description: '已定义的角色',
      icon: Shield,
      href: '/dashboard/roles',
    },
    {
      title: '权限数量',
      value: stats.permissions,
      description: '系统权限项',
      icon: Key,
      href: '/dashboard/permissions',
    },
    {
      title: '系统状态',
      value: systemStatus?.status === 'healthy' ? '正常' : '异常',
      description: systemStatus?.message || '检测中...',
      icon: Activity,
      href: '#',
    },
  ];

  /** 获取当前时间问候语 */
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return '早上好';
    if (hour < 18) return '下午好';
    return '晚上好';
  };

  return (
    <div className="space-y-6">
      {/* 欢迎区域 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {getGreeting()}，{user?.username || '管理员'}
          </h1>
          <p className="text-slate-500 mt-1">
            欢迎回到管理后台，这里是系统概览
          </p>
        </div>
        <Button
          variant="outline"
          onClick={loadStats}
          disabled={isLoading}
          className="gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          刷新数据
        </Button>
      </div>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <Card
              key={card.title}
              className="hover:shadow-md transition-shadow cursor-pointer"
            >
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">
                  {card.title}
                </CardTitle>
                <Icon className="h-5 w-5 text-slate-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-slate-900">
                  {isLoading ? (
                    <div className="h-8 w-16 bg-slate-200 animate-pulse rounded" />
                  ) : (
                    card.value
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-1">{card.description}</p>
                {card.href !== '#' && (
                  <Link
                    href={card.href}
                    className="inline-flex items-center text-xs text-blue-600 hover:text-blue-700 mt-2"
                  >
                    查看详情
                    <ArrowRight className="h-3 w-3 ml-1" />
                  </Link>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 快捷操作 */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* 快捷操作卡片 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">快捷操作</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link href="/dashboard/users">
              <Button variant="outline" className="w-full justify-start gap-3">
                <Users className="h-4 w-4" />
                管理用户
              </Button>
            </Link>
            <Link href="/dashboard/roles">
              <Button variant="outline" className="w-full justify-start gap-3">
                <Shield className="h-4 w-4" />
                管理角色
              </Button>
            </Link>
            <Link href="/dashboard/permissions">
              <Button variant="outline" className="w-full justify-start gap-3">
                <Key className="h-4 w-4" />
                管理权限
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* 系统信息卡片 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">系统信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">系统状态</span>
              <Badge
                variant={
                  systemStatus?.status === 'healthy' ? 'success' : 'destructive'
                }
              >
                {systemStatus?.status === 'healthy' ? '正常运行' : '状态异常'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">数据库连接</span>
              <Badge
                variant={
                  systemStatus?.database === 'connected' ? 'success' : 'destructive'
                }
              >
                {systemStatus?.database === 'connected' ? '已连接' : '未连接'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">API 版本</span>
              <span className="text-sm font-medium">
                {systemStatus?.version || 'N/A'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">当前登录</span>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-slate-400" />
                <span className="text-sm font-medium">{user?.email}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
