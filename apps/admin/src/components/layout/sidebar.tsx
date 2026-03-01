/**
 * 侧边栏导航组件
 * 
 * 提供主要的导航功能，包括 Dashboard、用户、角色、权限管理入口
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  Shield,
  Key,
  Settings,
  ChevronLeft,
  ChevronRight,
  FileText,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

/** 导航项配置 */
interface NavItem {
  /** 显示标题 */
  title: string;
  /** 路由路径 */
  href: string;
  /** 图标组件 */
  icon: React.ComponentType<{ className?: string }>;
  /** 描述文本 */
  description?: string;
}

/** 导航菜单配置 */
const navItems: NavItem[] = [
  {
    title: '仪表盘',
    href: '/dashboard',
    icon: LayoutDashboard,
    description: '系统概览与统计',
  },
  {
    title: '用户管理',
    href: '/dashboard/users',
    icon: Users,
    description: '管理系统用户',
  },
  {
    title: '角色管理',
    href: '/dashboard/roles',
    icon: Shield,
    description: '管理用户角色',
  },
  {
    title: '权限管理',
    href: '/dashboard/permissions',
    icon: Key,
    description: '管理系统权限',
  },
  {
    title: '审计日志',
    href: '/dashboard/audit-logs',
    icon: FileText,
    description: '查看操作记录',
  },
];

/** 底部导航项 */
const bottomNavItems: NavItem[] = [
  {
    title: '系统设置',
    href: '/dashboard/settings',
    icon: Settings,
    description: '系统配置',
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);

  /** 检查路由是否激活 */
  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard';
    }
    return pathname.startsWith(href);
  };

  return (
    <aside
      className={cn(
        'relative flex flex-col h-screen bg-slate-900 text-white border-r border-slate-800 transition-all duration-300',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo 区域 */}
      <div className="flex items-center h-16 px-4 border-b border-slate-800">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600">
            <Shield className="w-5 h-5 text-white" />
          </div>
          {!isCollapsed && (
            <span className="text-lg font-semibold tracking-tight">
              Admin Panel
            </span>
          )}
        </Link>
      </div>

      {/* 折叠按钮 */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-3 top-20 z-10 h-6 w-6 rounded-full border border-slate-700 bg-slate-800 hover:bg-slate-700"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        {isCollapsed ? (
          <ChevronRight className="h-3 w-3" />
        ) : (
          <ChevronLeft className="h-3 w-3" />
        )}
      </Button>

      {/* 主导航区域 */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                active
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )}
              title={isCollapsed ? item.title : undefined}
            >
              <Icon
                className={cn(
                  'w-5 h-5 flex-shrink-0',
                  active ? 'text-white' : 'text-slate-400'
                )}
              />
              {!isCollapsed && (
                <div className="flex-1 min-w-0">
                  <div className="truncate">{item.title}</div>
                  {item.description && (
                    <div className="text-xs text-slate-500 truncate">
                      {item.description}
                    </div>
                  )}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* 底部导航区域 */}
      <div className="px-3 py-4 border-t border-slate-800">
        {bottomNavItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                active
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )}
              title={isCollapsed ? item.title : undefined}
            >
              <Icon
                className={cn(
                  'w-5 h-5 flex-shrink-0',
                  active ? 'text-white' : 'text-slate-400'
                )}
              />
              {!isCollapsed && <span>{item.title}</span>}
            </Link>
          );
        })}
      </div>
    </aside>
  );
}
