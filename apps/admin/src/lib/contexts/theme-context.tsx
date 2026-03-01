/**
 * 主题上下文
 * 
 * 提供全局主题切换功能，支持浅色、深色和跟随系统三种模式
 */

'use client';

import { createContext, useContext, useEffect, useState } from 'react';

/** 主题类型 */
export type Theme = 'light' | 'dark' | 'system';

/** 主题上下文类型 */
interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'light' | 'dark';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/** 主题 Provider 组件 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('light');
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');

  /** 应用主题到 DOM */
  const applyTheme = (newTheme: Theme) => {
    const root = document.documentElement;
    let resolved: 'light' | 'dark' = 'light';

    if (newTheme === 'dark') {
      root.classList.add('dark');
      resolved = 'dark';
    } else if (newTheme === 'light') {
      root.classList.remove('dark');
      resolved = 'light';
    } else {
      // system
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (prefersDark) {
        root.classList.add('dark');
        resolved = 'dark';
      } else {
        root.classList.remove('dark');
        resolved = 'light';
      }
    }

    setResolvedTheme(resolved);
  };

  /** 设置主题 */
  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem('theme', newTheme);
    applyTheme(newTheme);
  };

  // 初始化主题
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    const initialTheme = savedTheme || 'light';
    setThemeState(initialTheme);
    applyTheme(initialTheme);
  }, []);

  // 监听系统主题变化
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (theme === 'system') {
        applyTheme('system');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  // 当主题设置为 system 时，监听系统变化
  useEffect(() => {
    if (theme === 'system') {
      applyTheme('system');
    }
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

/** 使用主题 Hook */
export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
