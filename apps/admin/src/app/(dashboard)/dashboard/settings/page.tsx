/**
 * 系统设置页面
 * 
 * 提供系统配置管理功能，包括主题设置、通知设置等
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Settings,
  Moon,
  Sun,
  Monitor,
  Bell,
  Globe,
  Database,
  Server,
  RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { statusApi } from '@/lib/api/status';
import { useToast } from '@/lib/hooks/use-toast';
import type { HealthStatus } from '@/types';

/** 主题类型 */
type Theme = 'light' | 'dark' | 'system';

/** 语言类型 */
type Language = 'zh-CN' | 'en-US';

/** 从 HealthStatus 数组中判断整体系统是否健康 */
function isSystemHealthy(statuses: HealthStatus[]): boolean {
  return statuses.length > 0 && statuses.every((s) => s.status === 'ok');
}

/** 从 HealthStatus 数组中查找指定服务的状态 */
function getServiceStatus(statuses: HealthStatus[], service: string): HealthStatus | undefined {
  return statuses.find((s) => s.service.toLowerCase().includes(service.toLowerCase()));
}

export default function SettingsPage() {
  const { toast } = useToast();
  
  // 系统状态
  const [healthStatuses, setHealthStatuses] = useState<HealthStatus[]>([]);
  const [isLoadingStatus, setIsLoadingStatus] = useState(true);

  // 设置状态
  const [theme, setTheme] = useState<Theme>('light');
  const [language, setLanguage] = useState<Language>('zh-CN');
  const [notifications, setNotifications] = useState({
    email: true,
    browser: true,
    sound: false,
  });

  /** 加载系统状态 */
  const loadSystemStatus = useCallback(async () => {
    setIsLoadingStatus(true);
    try {
      const statuses = await statusApi.getStatus();
      setHealthStatuses(statuses);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: '加载失败',
        description: '无法获取系统状态',
      });
    } finally {
      setIsLoadingStatus(false);
    }
  }, [toast]);

  useEffect(() => {
    loadSystemStatus();
    // 从 localStorage 加载设置
    const savedTheme = localStorage.getItem('theme') as Theme;
    const savedLanguage = localStorage.getItem('language') as Language;
    if (savedTheme) setTheme(savedTheme);
    if (savedLanguage) setLanguage(savedLanguage);
  }, [loadSystemStatus]);

  /** 保存主题设置 */
  const handleThemeChange = (newTheme: Theme) => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    
    // 应用主题
    const root = document.documentElement;
    if (newTheme === 'dark') {
      root.classList.add('dark');
    } else if (newTheme === 'light') {
      root.classList.remove('dark');
    } else {
      // system
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (prefersDark) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
    
    toast({
      title: '主题已更新',
      description: `已切换到${newTheme === 'light' ? '浅色' : newTheme === 'dark' ? '深色' : '系统'}主题`,
    });
  };

  /** 保存语言设置 */
  const handleLanguageChange = (newLanguage: Language) => {
    setLanguage(newLanguage);
    localStorage.setItem('language', newLanguage);
    toast({
      title: '语言已更新',
      description: `已切换到${newLanguage === 'zh-CN' ? '简体中文' : 'English'}`,
    });
  };

  /** 获取主题图标 */
  const getThemeIcon = (t: Theme) => {
    switch (t) {
      case 'light':
        return <Sun className="h-4 w-4" />;
      case 'dark':
        return <Moon className="h-4 w-4" />;
      case 'system':
        return <Monitor className="h-4 w-4" />;
    }
  };

  const healthy = isSystemHealthy(healthStatuses);
  const dbStatus = getServiceStatus(healthStatuses, 'mysql') || getServiceStatus(healthStatuses, 'postgres');
  const dbConnected = dbStatus?.status === 'ok';

  return (
    <div className="space-y-6 max-w-4xl">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">系统设置</h1>
        <p className="text-slate-500 mt-1">管理系统配置和个人偏好</p>
      </div>

      <div className="grid gap-6">
        {/* 外观设置 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sun className="h-5 w-5" />
              外观设置
            </CardTitle>
            <CardDescription>自定义系统的显示外观</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* 主题选择 */}
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label>主题模式</Label>
                <p className="text-sm text-slate-500">选择您喜欢的界面主题</p>
              </div>
              <div className="flex gap-2">
                {(['light', 'dark', 'system'] as Theme[]).map((t) => (
                  <Button
                    key={t}
                    variant={theme === t ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleThemeChange(t)}
                    className="gap-2"
                  >
                    {getThemeIcon(t)}
                    {t === 'light' ? '浅色' : t === 'dark' ? '深色' : '跟随系统'}
                  </Button>
                ))}
              </div>
            </div>

            {/* 语言选择 */}
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label className="flex items-center gap-2">
                  <Globe className="h-4 w-4 text-slate-400" />
                  界面语言
                </Label>
                <p className="text-sm text-slate-500">选择系统显示语言</p>
              </div>
              <Select value={language} onValueChange={(v) => handleLanguageChange(v as Language)}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="zh-CN">简体中文</SelectItem>
                  <SelectItem value="en-US">English</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* 通知设置 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              通知设置
            </CardTitle>
            <CardDescription>管理系统通知方式</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 邮件通知 */}
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium text-slate-900">邮件通知</p>
                <p className="text-sm text-slate-500">接收重要事件的邮件提醒</p>
              </div>
              <Button
                variant={notifications.email ? 'default' : 'outline'}
                size="sm"
                onClick={() => setNotifications({ ...notifications, email: !notifications.email })}
              >
                {notifications.email ? '已开启' : '已关闭'}
              </Button>
            </div>

            {/* 浏览器通知 */}
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium text-slate-900">浏览器通知</p>
                <p className="text-sm text-slate-500">在浏览器中显示桌面通知</p>
              </div>
              <Button
                variant={notifications.browser ? 'default' : 'outline'}
                size="sm"
                onClick={() => setNotifications({ ...notifications, browser: !notifications.browser })}
              >
                {notifications.browser ? '已开启' : '已关闭'}
              </Button>
            </div>

            {/* 声音提醒 */}
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium text-slate-900">声音提醒</p>
                <p className="text-sm text-slate-500">收到新消息时播放提示音</p>
              </div>
              <Button
                variant={notifications.sound ? 'default' : 'outline'}
                size="sm"
                onClick={() => setNotifications({ ...notifications, sound: !notifications.sound })}
              >
                {notifications.sound ? '已开启' : '已关闭'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 系统信息 */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Server className="h-5 w-5" />
                  系统信息
                </CardTitle>
                <CardDescription>查看系统运行状态</CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={loadSystemStatus}
                disabled={isLoadingStatus}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoadingStatus ? 'animate-spin' : ''}`} />
                刷新
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              {/* 系统状态 */}
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Server className="h-4 w-4 text-slate-400" />
                    <span className="text-sm font-medium">系统状态</span>
                  </div>
                  {isLoadingStatus ? (
                    <Badge variant="secondary">检测中...</Badge>
                  ) : (
                    <Badge variant={healthy ? 'success' : 'destructive'}>
                      {healthy ? '正常运行' : '状态异常'}
                    </Badge>
                  )}
                </div>
              </div>

              {/* 数据库状态 */}
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-slate-400" />
                    <span className="text-sm font-medium">数据库连接</span>
                  </div>
                  {isLoadingStatus ? (
                    <Badge variant="secondary">检测中...</Badge>
                  ) : (
                    <Badge variant={dbConnected ? 'success' : 'destructive'}>
                      {dbConnected ? '已连接' : '未连接'}
                    </Badge>
                  )}
                </div>
              </div>

              {/* 各服务状态 */}
              {healthStatuses.map((s) => (
                <div key={s.service} className="p-4 bg-slate-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Settings className="h-4 w-4 text-slate-400" />
                      <span className="text-sm font-medium">{s.service}</span>
                    </div>
                    <Badge variant={s.status === 'ok' ? 'success' : 'destructive'}>
                      {s.status === 'ok' ? '正常' : '异常'}
                    </Badge>
                  </div>
                  {s.details && (
                    <p className="text-xs text-slate-500 mt-1 ml-6">{s.details}</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 关于 */}
        <Card>
          <CardHeader>
            <CardTitle>关于系统</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-slate-600 space-y-2">
              <p><strong>用户权限管理系统</strong></p>
              <p>版本：1.0.0</p>
              <p>一个现代化的企业级用户权限管理后台，基于 Next.js 14 + TypeScript + Tailwind CSS 构建。</p>
              <p className="text-slate-400 mt-4">
                Copyright &copy; {new Date().getFullYear()} All rights reserved.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
