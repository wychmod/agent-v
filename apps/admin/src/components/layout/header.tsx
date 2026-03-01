/**
 * 顶部导航栏组件
 * 
 * 显示当前页面标题、用户信息和操作菜单
 */

'use client';

import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import {
  Bell,
  Search,
  LogOut,
  User,
  Settings,
  ChevronDown,
  Moon,
  Sun,
} from 'lucide-react';
import { useAuthStore } from '@/lib/store/auth-store';
import { logout } from '@/lib/api/auth';
import { useTheme } from '@/lib/contexts/theme-context';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { useToast } from '@/lib/hooks/use-toast';
import { GlobalSearch } from '@/components/global-search';

export function Header() {
  const router = useRouter();
  const { toast } = useToast();
  const { user, refreshToken, clearAuth } = useAuthStore();
  const { setTheme, resolvedTheme, mounted } = useTheme();
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  // 监听快捷键 Ctrl/Cmd + K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsSearchOpen(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  /** 处理登出 */
  const handleLogout = async () => {
    try {
      // 调用后端登出 API，传递 refreshToken 以使其失效
      await logout(refreshToken ?? undefined);
    } catch (error) {
      // 即使 API 调用失败，也继续清除本地状态
      console.error('登出 API 调用失败:', error);
    }
    clearAuth();
    toast({
      title: '已登出',
      description: '您已成功退出系统',
    });
    router.push('/login');
  };

  /** 获取用户名首字母 */
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  /** 切换主题 */
  const toggleTheme = () => {
    if (resolvedTheme === 'dark') {
      setTheme('light');
    } else {
      setTheme('dark');
    }
  };

  return (
    <>
      <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-6 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
      {/* 左侧：搜索按钮 */}
      <div className="flex items-center gap-4 flex-1 max-w-md">
        <button
          onClick={() => setIsSearchOpen(true)}
          className="flex items-center gap-3 w-full px-3 py-2 text-sm text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
        >
          <Search className="h-4 w-4" />
          <span className="flex-1 text-left">搜索...</span>
          <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 text-xs font-mono bg-slate-200 dark:bg-slate-700 rounded">
            ⌘K
          </kbd>
        </button>
      </div>

      {/* 右侧：主题切换、通知和用户菜单 */}
      <div className="flex items-center gap-4">
        {/* 主题切换按钮 */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="text-slate-600 dark:text-slate-400"
        >
          {mounted && resolvedTheme === 'dark' ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </Button>

        {/* 通知按钮 */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5 text-slate-600 dark:text-slate-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </Button>

        {/* 用户下拉菜单 */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="flex items-center gap-3 h-auto py-2 px-3 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white text-sm">
                  {user?.username ? getInitials(user.username) : 'U'}
                </AvatarFallback>
              </Avatar>
              <div className="hidden md:flex flex-col items-start">
                <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {user?.username || '未知用户'}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {user?.email || ''}
                </span>
              </div>
              <ChevronDown className="h-4 w-4 text-slate-400" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">{user?.username}</p>
                <p className="text-xs text-slate-500">{user?.email}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => router.push('/dashboard/profile')}>
              <User className="mr-2 h-4 w-4" />
              <span>个人资料</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push('/dashboard/settings')}>
              <Settings className="mr-2 h-4 w-4" />
              <span>设置</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleLogout}
              className="text-red-600 focus:text-red-600 focus:bg-red-50"
            >
              <LogOut className="mr-2 h-4 w-4" />
              <span>退出登录</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>

    {/* 全局搜索对话框 */}
    <GlobalSearch open={isSearchOpen} onOpenChange={setIsSearchOpen} />
    </>
  );
}
