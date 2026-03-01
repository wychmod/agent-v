/**
 * Dashboard 布局
 * 
 * 包含侧边栏和顶部导航栏的主布局结构
 * 所有 Dashboard 子页面都使用此布局
 */

'use client';

import { Sidebar, Header } from '@/components/layout';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
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
