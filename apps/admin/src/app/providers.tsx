/**
 * 全局 Providers 组件
 * 
 * 包装 React Query、Theme 和 Toast 等全局 Provider
 */

'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { Toaster } from '@/components/ui/toaster';
import { ThemeProvider } from '@/lib/contexts/theme-context';
import { useAuthStore } from '@/lib/store/auth-store';

/** 存储 Hydration 组件 - 在客户端手动触发 rehydrate */
function StoreHydration() {
  useEffect(() => {
    useAuthStore.persist.rehydrate();
  }, []);
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000, // 30 秒
            gcTime: 5 * 60 * 1000, // 5 分钟
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <StoreHydration />
        {children}
        <Toaster />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
