/**
 * 个人资料页面
 * 
 * 显示和编辑当前用户的个人信息，支持修改密码功能
 */

'use client';

import { useState } from 'react';
import { AxiosError } from 'axios';
import {
  User,
  Mail,
  Shield,
  Calendar,
  Lock,
  Save,
  Eye,
  EyeOff,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuthStore } from '@/lib/store/auth-store';
import { usersApi } from '@/lib/api/users';
import { useToast } from '@/lib/hooks/use-toast';
import { formatDateTime } from '@/lib/utils';

export default function ProfilePage() {
  const { user, setUser } = useAuthStore();
  const { toast } = useToast();
  
  // 编辑状态
  const [isEditing, setIsEditing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
  });

  // 修改密码对话框状态
  const [isPasswordDialogOpen, setIsPasswordDialogOpen] = useState(false);
  const [showPassword, setShowPassword] = useState({
    old: false,
    new: false,
    confirm: false,
  });
  const [passwordData, setPasswordData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  /** 获取用户名首字母 */
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  /** 保存个人信息 */
  const handleSaveProfile = async () => {
    if (!user) return;

    setIsSubmitting(true);
    try {
      const updatedDetail = await usersApi.updateUser(user.id, {
        username: formData.username,
        email: formData.email,
      });
      // 将 UserDetail 映射为 UserInfo（auth store 存储的格式）
      setUser({
        id: updatedDetail.id,
        email: updatedDetail.email,
        username: updatedDetail.username,
        is_active: updatedDetail.is_active,
        is_verified: updatedDetail.is_verified,
        must_change_password: updatedDetail.must_change_password,
        roles: updatedDetail.roles.map((r) => r.name),
        created_at: updatedDetail.created_at,
      });
      toast({
        title: '保存成功',
        description: '个人信息已更新',
      });
      setIsEditing(false);
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '保存失败',
        description: axiosError.response?.data?.detail || '无法更新个人信息',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 修改密码 */
  const handleChangePassword = async () => {
    // 验证
    if (!passwordData.oldPassword || !passwordData.newPassword) {
      toast({
        variant: 'destructive',
        title: '验证失败',
        description: '请填写所有密码字段',
      });
      return;
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast({
        variant: 'destructive',
        title: '验证失败',
        description: '两次输入的新密码不一致',
      });
      return;
    }

    if (passwordData.newPassword.length < 6) {
      toast({
        variant: 'destructive',
        title: '验证失败',
        description: '新密码长度至少为6位',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await usersApi.changePassword(passwordData.oldPassword, passwordData.newPassword);
      toast({
        title: '修改成功',
        description: '密码已更新，请使用新密码登录',
      });
      setIsPasswordDialogOpen(false);
      setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' });
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '修改失败',
        description: axiosError.response?.data?.detail || '原密码不正确或无法修改密码',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 取消编辑 */
  const handleCancelEdit = () => {
    setFormData({
      username: user?.username || '',
      email: user?.email || '',
    });
    setIsEditing(false);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">个人资料</h1>
        <p className="text-slate-500 mt-1">查看和管理您的个人信息</p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* 左侧：用户头像卡片 */}
        <Card className="md:col-span-1">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center text-center">
              <Avatar className="h-24 w-24 mb-4">
                <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white text-2xl">
                  {user?.username ? getInitials(user.username) : 'U'}
                </AvatarFallback>
              </Avatar>
              <h3 className="text-lg font-semibold text-slate-900">
                {user?.username || '未知用户'}
              </h3>
              <p className="text-sm text-slate-500">{user?.email}</p>
              <div className="flex gap-2 mt-3">
                {user?.is_active ? (
                  <Badge variant="success">账户活跃</Badge>
                ) : (
                  <Badge variant="destructive">账户禁用</Badge>
                )}
                {user?.is_verified && (
                  <Badge variant="secondary">已验证</Badge>
                )}
              </div>
              {/* 用户角色（roles 为字符串数组） */}
              {user?.roles && user.roles.length > 0 && (
                <div className="mt-4 w-full">
                  <p className="text-xs text-slate-400 mb-2">角色</p>
                  <div className="flex flex-wrap justify-center gap-1">
                    {user.roles.map((roleName) => (
                      <Badge key={roleName} variant="outline" className="text-xs">
                        <Shield className="h-3 w-3 mr-1" />
                        {roleName}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 右侧：个人信息表单 */}
        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>基本信息</CardTitle>
                <CardDescription>您的账户基本信息</CardDescription>
              </div>
              {!isEditing ? (
                <Button variant="outline" onClick={() => setIsEditing(true)}>
                  编辑资料
                </Button>
              ) : (
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleCancelEdit}>
                    取消
                  </Button>
                  <Button onClick={handleSaveProfile} disabled={isSubmitting}>
                    <Save className="h-4 w-4 mr-2" />
                    {isSubmitting ? '保存中...' : '保存'}
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 用户名 */}
            <div className="space-y-2">
              <Label htmlFor="username" className="flex items-center gap-2">
                <User className="h-4 w-4 text-slate-400" />
                用户名
              </Label>
              {isEditing ? (
                <Input
                  id="username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  placeholder="请输入用户名"
                />
              ) : (
                <p className="text-sm text-slate-700 py-2">{user?.username || '-'}</p>
              )}
            </div>

            {/* 邮箱 */}
            <div className="space-y-2">
              <Label htmlFor="email" className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-slate-400" />
                邮箱地址
              </Label>
              {isEditing ? (
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="请输入邮箱"
                />
              ) : (
                <p className="text-sm text-slate-700 py-2">{user?.email || '-'}</p>
              )}
            </div>

            {/* 创建时间 */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-slate-400" />
                注册时间
              </Label>
              <p className="text-sm text-slate-700 py-2">
                {user?.created_at ? formatDateTime(user.created_at) : '-'}
              </p>
            </div>

            {/* 用户 ID */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2 text-slate-400">
                用户 ID
              </Label>
              <p className="text-xs text-slate-400 font-mono py-2">
                {user?.id || '-'}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* 安全设置卡片 */}
        <Card className="md:col-span-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="h-5 w-5" />
              安全设置
            </CardTitle>
            <CardDescription>管理您的账户安全选项</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium text-slate-900">登录密码</p>
                <p className="text-sm text-slate-500">定期更改密码可以提高账户安全性</p>
              </div>
              <Button variant="outline" onClick={() => setIsPasswordDialogOpen(true)}>
                修改密码
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 修改密码对话框 */}
      <Dialog open={isPasswordDialogOpen} onOpenChange={setIsPasswordDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Lock className="h-5 w-5" />
              修改密码
            </DialogTitle>
            <DialogDescription>
              请输入当前密码和新密码来更新您的登录凭证
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* 当前密码 */}
            <div className="space-y-2">
              <Label htmlFor="old-password">当前密码</Label>
              <div className="relative">
                <Input
                  id="old-password"
                  type={showPassword.old ? 'text' : 'password'}
                  value={passwordData.oldPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, oldPassword: e.target.value })}
                  placeholder="请输入当前密码"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full"
                  onClick={() => setShowPassword({ ...showPassword, old: !showPassword.old })}
                >
                  {showPassword.old ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            {/* 新密码 */}
            <div className="space-y-2">
              <Label htmlFor="new-password">新密码</Label>
              <div className="relative">
                <Input
                  id="new-password"
                  type={showPassword.new ? 'text' : 'password'}
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                  placeholder="请输入新密码（至少6位）"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full"
                  onClick={() => setShowPassword({ ...showPassword, new: !showPassword.new })}
                >
                  {showPassword.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>

            {/* 确认新密码 */}
            <div className="space-y-2">
              <Label htmlFor="confirm-password">确认新密码</Label>
              <div className="relative">
                <Input
                  id="confirm-password"
                  type={showPassword.confirm ? 'text' : 'password'}
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                  placeholder="请再次输入新密码"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full"
                  onClick={() => setShowPassword({ ...showPassword, confirm: !showPassword.confirm })}
                >
                  {showPassword.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsPasswordDialogOpen(false);
                setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' });
              }}
            >
              取消
            </Button>
            <Button onClick={handleChangePassword} disabled={isSubmitting}>
              {isSubmitting ? '修改中...' : '确认修改'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
