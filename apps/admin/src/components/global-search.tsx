/**
 * 全局搜索组件
 * 
 * 提供全局快速搜索功能，支持搜索用户、角色、权限等资源
 * 支持键盘快捷键 Ctrl/Cmd + K 打开搜索
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Search,
  Users,
  Shield,
  Key,
  FileText,
  Settings,
  User,
  LayoutDashboard,
  X,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

/** 搜索结果项类型 */
interface SearchResult {
  id: string;
  title: string;
  description?: string;
  type: 'page' | 'user' | 'role' | 'permission' | 'action';
  icon: React.ComponentType<{ className?: string }>;
  href?: string;
  action?: () => void;
}

/** 预定义的页面导航 */
const PAGES: SearchResult[] = [
  {
    id: 'dashboard',
    title: '仪表盘',
    description: '查看系统概览',
    type: 'page',
    icon: LayoutDashboard,
    href: '/dashboard',
  },
  {
    id: 'users',
    title: '用户管理',
    description: '管理系统用户',
    type: 'page',
    icon: Users,
    href: '/dashboard/users',
  },
  {
    id: 'roles',
    title: '角色管理',
    description: '管理用户角色',
    type: 'page',
    icon: Shield,
    href: '/dashboard/roles',
  },
  {
    id: 'permissions',
    title: '权限管理',
    description: '管理系统权限',
    type: 'page',
    icon: Key,
    href: '/dashboard/permissions',
  },
  {
    id: 'audit-logs',
    title: '审计日志',
    description: '查看操作记录',
    type: 'page',
    icon: FileText,
    href: '/dashboard/audit-logs',
  },
  {
    id: 'profile',
    title: '个人资料',
    description: '查看和编辑个人信息',
    type: 'page',
    icon: User,
    href: '/dashboard/profile',
  },
  {
    id: 'settings',
    title: '系统设置',
    description: '管理系统配置',
    type: 'page',
    icon: Settings,
    href: '/dashboard/settings',
  },
];

interface GlobalSearchProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function GlobalSearch({ open, onOpenChange }: GlobalSearchProps) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>(PAGES);
  const [selectedIndex, setSelectedIndex] = useState(0);

  /** 搜索过滤 */
  useEffect(() => {
    if (!query.trim()) {
      setResults(PAGES);
      return;
    }

    const lowerQuery = query.toLowerCase();
    const filtered = PAGES.filter(
      (item) =>
        item.title.toLowerCase().includes(lowerQuery) ||
        item.description?.toLowerCase().includes(lowerQuery)
    );
    setResults(filtered);
    setSelectedIndex(0);
  }, [query]);

  /** 执行搜索结果操作 */
  const executeResult = useCallback(
    (result: SearchResult) => {
      if (result.href) {
        router.push(result.href);
      } else if (result.action) {
        result.action();
      }
      onOpenChange(false);
      setQuery('');
    },
    [router, onOpenChange]
  );

  /** 键盘导航 */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev < results.length - 1 ? prev + 1 : prev
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : prev));
          break;
        case 'Enter':
          e.preventDefault();
          if (results[selectedIndex]) {
            executeResult(results[selectedIndex]);
          }
          break;
        case 'Escape':
          onOpenChange(false);
          break;
      }
    },
    [results, selectedIndex, executeResult, onOpenChange]
  );

  /** 重置状态 */
  useEffect(() => {
    if (!open) {
      setQuery('');
      setSelectedIndex(0);
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg p-0 gap-0 overflow-hidden">
        {/* 搜索输入框 */}
        <div className="flex items-center border-b px-4 dark:border-slate-800">
          <Search className="h-4 w-4 text-slate-400 shrink-0" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="搜索页面..."
            className="h-12 border-0 focus-visible:ring-0 px-3"
            autoFocus
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded"
            >
              <X className="h-4 w-4 text-slate-400" />
            </button>
          )}
        </div>

        {/* 搜索结果列表 */}
        <div className="max-h-80 overflow-y-auto p-2">
          {results.length === 0 ? (
            <div className="py-8 text-center text-sm text-slate-500">
              没有找到匹配的结果
            </div>
          ) : (
            <div className="space-y-1">
              {results.map((result, index) => {
                const Icon = result.icon;
                return (
                  <button
                    key={result.id}
                    onClick={() => executeResult(result)}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={cn(
                      'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors',
                      index === selectedIndex
                        ? 'bg-blue-50 dark:bg-blue-900/20'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-800'
                    )}
                  >
                    <div
                      className={cn(
                        'flex items-center justify-center w-8 h-8 rounded-lg',
                        index === selectedIndex
                          ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400'
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p
                        className={cn(
                          'font-medium text-sm',
                          index === selectedIndex
                            ? 'text-blue-700 dark:text-blue-300'
                            : 'text-slate-900 dark:text-slate-100'
                        )}
                      >
                        {result.title}
                      </p>
                      {result.description && (
                        <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                          {result.description}
                        </p>
                      )}
                    </div>
                    {index === selectedIndex && (
                      <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 text-xs font-mono bg-slate-100 dark:bg-slate-800 text-slate-500 rounded">
                        Enter
                      </kbd>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* 底部提示 */}
        <div className="flex items-center justify-between px-4 py-2 border-t dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <kbd className="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded">↑</kbd>
            <kbd className="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded">↓</kbd>
            <span>导航</span>
          </div>
          <div className="flex items-center gap-2">
            <kbd className="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded">Enter</kbd>
            <span>选择</span>
          </div>
          <div className="flex items-center gap-2">
            <kbd className="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded">Esc</kbd>
            <span>关闭</span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
