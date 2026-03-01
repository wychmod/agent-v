/**
 * 首页重定向
 * 
 * 根据用户认证状态自动重定向到 Dashboard 或登录页
 */

import { redirect } from 'next/navigation';

export default function Home() {
  // 重定向到 Dashboard，中间件会根据认证状态处理跳转
  redirect('/dashboard');
}
