/**
 * 登录页面
 * 
 * 使用 dynamic import 禁用 SSR，完全避免 hydration 问题
 */

import dynamic from 'next/dynamic';

// 禁用 SSR，组件只在客户端渲染
const LoginForm = dynamic(() => import('./login-form'), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="w-full max-w-md mx-4 h-96 rounded-lg bg-slate-800/50 animate-pulse"></div>
    </div>
  ),
});

export default function LoginPage() {
  return <LoginForm />;
}
