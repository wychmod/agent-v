/**
 * Next.js 中间件
 * 用于路由保护和认证检查
 */

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// 公开路由列表（无需认证）
const PUBLIC_ROUTES = ['/login', '/forgot-password', '/reset-password']

// 认证路由列表（已登录用户不应访问）
const AUTH_ROUTES = ['/login']

/**
 * 中间件函数
 * 检查用户认证状态并进行路由保护
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // 获取认证 token（从 localStorage 持久化的 cookie 或直接检查）
  // 注意：Zustand persist 使用 localStorage，中间件无法直接访问
  // 因此我们使用一个简单的 cookie 来同步认证状态
  const authToken = request.cookies.get('auth-token')?.value

  const isAuthenticated = !!authToken
  const isPublicRoute = PUBLIC_ROUTES.some(route => pathname.startsWith(route))
  const isAuthRoute = AUTH_ROUTES.some(route => pathname.startsWith(route))

  // 如果是 API 路由或静态资源，直接放行
  if (
    pathname.startsWith('/api') ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/favicon') ||
    pathname.includes('.')
  ) {
    return NextResponse.next()
  }

  // 已登录用户访问认证页面，重定向到 dashboard
  if (isAuthenticated && isAuthRoute) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  // 未登录用户访问受保护路由，重定向到登录页
  if (!isAuthenticated && !isPublicRoute) {
    const loginUrl = new URL('/login', request.url)
    // 保存原始请求路径，登录后可以重定向回来
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

/**
 * 配置中间件匹配的路由
 */
export const config = {
  matcher: [
    /*
     * 匹配所有路径，除了以下开头的：
     * - api (API 路由)
     * - _next/static (静态文件)
     * - _next/image (图片优化文件)
     * - favicon.ico (网站图标)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
