/**
 * Dashboard 布局
 * 
 * 包含侧边栏和顶部导航栏的主布局结构
 * 所有 Dashboard 子页面都使用此布局
 */

'use client';

import { useTheme } from '@/lib/contexts/theme-context';
import { Sidebar, Header } from '@/components/layout';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { mounted } = useTheme();

  // 防止 hydration 不匹配，挂载前显示占位
  if (!mounted) {
    return (
      <div className="flex h-screen bg-slate-50">
        {/* 侧边栏占位 */}
        <div className="w-64 h-screen bg-slate-900" />
        {/* 主内容区域占位 */}
        <div className="flex flex-col flex-1 overflow-hidden">
          <div className="h-16 bg-white border-b border-slate-200" />
          <main className="flex-1 overflow-y-auto p-6" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950">
      {/* 侧边栏 */}
      <Sidebar />

      {/* 主内容区域 */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* 顶部导航栏 */}
        <Header />

        {/* 页面内容 */}
        <main className="flex-1 overflow-y-auto p-6 dark:bg-slate-900">
          {children}
        </main>
      </div>
    </div>
  );
}
