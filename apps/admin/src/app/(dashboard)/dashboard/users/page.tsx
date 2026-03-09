/**
 * 用户管理页面
 * 
 * 提供用户列表展示、搜索、分页、创建、编辑、删除等功能
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { AxiosError } from 'axios';
import {
  Search,
  Plus,
  Edit,
  Trash2,
  Shield,
  MoreHorizontal,
  RefreshCw,
  UserPlus,
  Download,
  CheckSquare,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { usersApi } from '@/lib/api/users';
import { rolesApi } from '@/lib/api/roles';
import { useToast } from '@/lib/hooks/use-toast';
import { formatDateTime } from '@/lib/utils';
import type { UserDetail, Role, AdminCreateUserRequest, AdminUpdateUserRequest } from '@/types';

export default function UsersPage() {
  const { toast } = useToast();

  // 状态管理
  const [users, setUsers] = useState<UserDetail[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const pageSize = 10;

  // 对话框状态
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isAssignRoleDialogOpen, setIsAssignRoleDialogOpen] = useState(false);
  const [isBatchDeleteDialogOpen, setIsBatchDeleteDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserDetail | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 批量选择状态
  const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set());

  // 表单状态
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    is_active: true,
  });
  const [selectedRoleName, setSelectedRoleName] = useState('');

  /** 加载用户列表 */
  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await usersApi.getUsers({
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
      });

      setUsers(response.items || []);
      setTotalItems(response.total || 0);
      setTotalPages(Math.ceil((response.total || 0) / pageSize));
    } catch (error) {
      toast({
        variant: 'destructive',
        title: '加载失败',
        description: '无法加载用户列表，请稍后重试',
      });
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, toast]);

  /** 加载角色列表 */
  const loadRoles = useCallback(async () => {
    try {
      const response = await rolesApi.getRoles();
      setRoles(response || []);
    } catch (error) {
      console.error('加载角色列表失败:', error);
    }
  }, []);

  useEffect(() => {
    loadUsers();
    loadRoles();
  }, [loadUsers, loadRoles]);

  /** 处理搜索 */
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    loadUsers();
  };

  /** 重置表单 */
  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      password: '',
      is_active: true,
    });
    setSelectedRoleName('');
  };

  /** 打开创建对话框 */
  const openCreateDialog = () => {
    resetForm();
    setIsCreateDialogOpen(true);
  };

  /** 打开编辑对话框 */
  const openEditDialog = (user: UserDetail) => {
    setSelectedUser(user);
    setFormData({
      username: user.username,
      email: user.email,
      password: '',
      is_active: user.is_active,
    });
    setIsEditDialogOpen(true);
  };

  /** 打开删除确认对话框 */
  const openDeleteDialog = (user: UserDetail) => {
    setSelectedUser(user);
    setIsDeleteDialogOpen(true);
  };

  /** 打开分配角色对话框 */
  const openAssignRoleDialog = (user: UserDetail) => {
    setSelectedUser(user);
    setSelectedRoleName('');
    setIsAssignRoleDialogOpen(true);
  };

  /** 创建用户 */
  const handleCreateUser = async () => {
    if (!formData.username || !formData.email || !formData.password) {
      toast({
        variant: 'destructive',
        title: '验证失败',
        description: '请填写所有必填字段',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const data: AdminCreateUserRequest = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        is_active: formData.is_active,
      };

      await usersApi.createUser(data);
      toast({
        title: '创建成功',
        description: `用户 ${formData.username} 已成功创建`,
      });
      setIsCreateDialogOpen(false);
      loadUsers();
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '创建失败',
        description: axiosError.response?.data?.detail || '无法创建用户',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 更新用户 */
  const handleUpdateUser = async () => {
    if (!selectedUser) return;

    setIsSubmitting(true);
    try {
      const data: AdminUpdateUserRequest = {
        username: formData.username || undefined,
        email: formData.email || undefined,
        is_active: formData.is_active,
      };

      await usersApi.updateUser(selectedUser.id, data);
      toast({
        title: '更新成功',
        description: `用户信息已更新`,
      });
      setIsEditDialogOpen(false);
      loadUsers();
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '更新失败',
        description: axiosError.response?.data?.detail || '无法更新用户',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 删除用户 */
  const handleDeleteUser = async () => {
    if (!selectedUser) return;

    setIsSubmitting(true);
    try {
      await usersApi.deleteUser(selectedUser.id);
      toast({
        title: '删除成功',
        description: `用户 ${selectedUser.username} 已被删除`,
      });
      setIsDeleteDialogOpen(false);
      loadUsers();
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '删除失败',
        description: axiosError.response?.data?.detail || '无法删除用户',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 分配角色（使用角色名称） */
  const handleAssignRole = async () => {
    if (!selectedUser || !selectedRoleName) return;

    setIsSubmitting(true);
    try {
      await usersApi.assignRole(selectedUser.id, selectedRoleName);
      toast({
        title: '分配成功',
        description: '角色已成功分配给用户',
      });
      setIsAssignRoleDialogOpen(false);
      loadUsers();
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '分配失败',
        description: axiosError.response?.data?.detail || '无法分配角色',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 移除角色（使用角色名称） */
  const handleRemoveRole = async (user: UserDetail, roleName: string) => {
    try {
      await usersApi.removeRole(user.id, roleName);
      toast({
        title: '移除成功',
        description: '角色已从用户移除',
      });
      loadUsers();
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '移除失败',
        description: axiosError.response?.data?.detail || '无法移除角色',
      });
    }
  };

  /** 切换用户选中状态 */
  const toggleUserSelection = (userId: string) => {
    const newSelected = new Set(selectedUsers);
    if (newSelected.has(userId)) {
      newSelected.delete(userId);
    } else {
      newSelected.add(userId);
    }
    setSelectedUsers(newSelected);
  };

  /** 切换全选状态 */
  const toggleSelectAll = () => {
    if (selectedUsers.size === users.length) {
      setSelectedUsers(new Set());
    } else {
      setSelectedUsers(new Set(users.map((u) => u.id)));
    }
  };

  /** 批量删除用户 */
  const handleBatchDelete = async () => {
    if (selectedUsers.size === 0) return;

    setIsSubmitting(true);
    try {
      // 并行删除所有选中的用户
      await Promise.all(
        Array.from(selectedUsers).map((userId) => usersApi.deleteUser(userId))
      );
      toast({
        title: '批量删除成功',
        description: `已删除 ${selectedUsers.size} 个用户`,
      });
      setSelectedUsers(new Set());
      setIsBatchDeleteDialogOpen(false);
      loadUsers();
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '批量删除失败',
        description: axiosError.response?.data?.detail || '部分用户删除失败',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 导出用户数据为 CSV */
  const handleExportCSV = () => {
    const headers = ['用户名', '邮箱', '状态', '角色', '创建时间'];
    const rows = users.map((user) => [
      user.username,
      user.email,
      user.is_active ? '活跃' : '禁用',
      user.roles?.map((r) => r.display_name || r.name).join('; ') || '无',
      user.created_at,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `users_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();

    toast({
      title: '导出成功',
      description: `已导出 ${users.length} 条用户数据`,
    });
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">用户管理</h1>
          <p className="text-slate-500 mt-1">管理系统中的所有用户账户</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleExportCSV} className="gap-2">
            <Download className="h-4 w-4" />
            导出
          </Button>
          <Button onClick={openCreateDialog} className="gap-2">
            <Plus className="h-4 w-4" />
            新建用户
          </Button>
        </div>
      </div>

      {/* 搜索和筛选 */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                type="search"
                placeholder="搜索用户名或邮箱..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button type="submit" variant="secondary">
              搜索
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setSearchQuery('');
                setCurrentPage(1);
                loadUsers();
              }}
            >
              重置
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={loadUsers}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* 批量操作栏 */}
      {selectedUsers.size > 0 && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckSquare className="h-4 w-4 text-blue-600" />
                <span className="text-sm text-blue-700">
                  已选择 {selectedUsers.size} 个用户
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedUsers(new Set())}
                >
                  取消选择
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setIsBatchDeleteDialogOpen(true)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  批量删除
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 用户列表 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium">
            用户列表
            <span className="ml-2 text-sm font-normal text-slate-500">
              共 {totalItems} 条记录
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">
                  <input
                    type="checkbox"
                    checked={users.length > 0 && selectedUsers.size === users.length}
                    onChange={toggleSelectAll}
                    className="h-4 w-4 rounded border-slate-300"
                  />
                </TableHead>
                <TableHead>用户名</TableHead>
                <TableHead>邮箱</TableHead>
                <TableHead>角色</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>创建时间</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-10">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto text-slate-400" />
                    <p className="mt-2 text-sm text-slate-500">加载中...</p>
                  </TableCell>
                </TableRow>
              ) : users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-10">
                    <p className="text-sm text-slate-500">暂无用户数据</p>
                  </TableCell>
                </TableRow>
              ) : (
                users.map((user) => (
                  <TableRow key={user.id} className={selectedUsers.has(user.id) ? 'bg-blue-50' : ''}>
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={selectedUsers.has(user.id)}
                        onChange={() => toggleUserSelection(user.id)}
                        className="h-4 w-4 rounded border-slate-300"
                      />
                    </TableCell>
                    <TableCell className="font-medium">{user.username}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {user.roles && user.roles.length > 0 ? (
                          user.roles.map((role) => (
                            <Badge
                              key={role.id}
                              variant="secondary"
                              className="cursor-pointer hover:bg-slate-200"
                              onClick={() => handleRemoveRole(user, role.name)}
                              title="点击移除此角色"
                            >
                              {role.display_name || role.name}
                            </Badge>
                          ))
                        ) : (
                          <span className="text-slate-400 text-sm">无角色</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.is_active ? 'success' : 'destructive'}>
                        {user.is_active ? '活跃' : '禁用'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500">
                      {formatDateTime(user.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEditDialog(user)}>
                            <Edit className="mr-2 h-4 w-4" />
                            编辑
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openAssignRoleDialog(user)}>
                            <Shield className="mr-2 h-4 w-4" />
                            分配角色
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => openDeleteDialog(user)}
                            className="text-red-600 focus:text-red-600 focus:bg-red-50"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            删除
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <p className="text-sm text-slate-500">
                第 {currentPage} 页，共 {totalPages} 页
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  上一页
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 创建用户对话框 */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5" />
              新建用户
            </DialogTitle>
            <DialogDescription>创建一个新的系统用户账户</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="create-username">用户名 *</Label>
              <Input
                id="create-username"
                value={formData.username}
                onChange={(e) =>
                  setFormData({ ...formData, username: e.target.value })
                }
                placeholder="请输入用户名"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-email">邮箱 *</Label>
              <Input
                id="create-email"
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                placeholder="请输入邮箱地址"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-password">密码 *</Label>
              <Input
                id="create-password"
                type="password"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                placeholder="请输入密码"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="create-active"
                checked={formData.is_active}
                onChange={(e) =>
                  setFormData({ ...formData, is_active: e.target.checked })
                }
                className="h-4 w-4 rounded border-slate-300"
              />
              <Label htmlFor="create-active" className="font-normal">
                账户激活状态
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsCreateDialogOpen(false)}
            >
              取消
            </Button>
            <Button onClick={handleCreateUser} disabled={isSubmitting}>
              {isSubmitting ? '创建中...' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑用户对话框 */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Edit className="h-5 w-5" />
              编辑用户
            </DialogTitle>
            <DialogDescription>
              修改用户 {selectedUser?.username} 的信息
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-username">用户名</Label>
              <Input
                id="edit-username"
                value={formData.username}
                onChange={(e) =>
                  setFormData({ ...formData, username: e.target.value })
                }
                placeholder="请输入用户名"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-email">邮箱</Label>
              <Input
                id="edit-email"
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                placeholder="请输入邮箱地址"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="edit-active"
                checked={formData.is_active}
                onChange={(e) =>
                  setFormData({ ...formData, is_active: e.target.checked })
                }
                className="h-4 w-4 rounded border-slate-300"
              />
              <Label htmlFor="edit-active" className="font-normal">
                账户激活状态
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleUpdateUser} disabled={isSubmitting}>
              {isSubmitting ? '保存中...' : '保存'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除用户</AlertDialogTitle>
            <AlertDialogDescription>
              您确定要删除用户 <strong>{selectedUser?.username}</strong> 吗？
              此操作无法撤销，该用户的所有数据将被永久删除。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteUser}
              className="bg-red-600 hover:bg-red-700"
            >
              {isSubmitting ? '删除中...' : '确认删除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 分配角色对话框（使用角色名称） */}
      <Dialog open={isAssignRoleDialogOpen} onOpenChange={setIsAssignRoleDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              分配角色
            </DialogTitle>
            <DialogDescription>
              为用户 {selectedUser?.username} 分配角色
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>选择角色</Label>
              <Select value={selectedRoleName} onValueChange={setSelectedRoleName}>
                <SelectTrigger>
                  <SelectValue placeholder="请选择一个角色" />
                </SelectTrigger>
                <SelectContent>
                  {roles.map((role) => (
                    <SelectItem key={role.id} value={role.name}>
                      {role.display_name || role.name}
                      {role.description && (
                        <span className="text-slate-400 ml-2">
                          - {role.description}
                        </span>
                      )}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selectedUser?.roles && selectedUser.roles.length > 0 && (
              <div className="space-y-2">
                <Label>当前角色</Label>
                <div className="flex flex-wrap gap-2">
                  {selectedUser.roles.map((role) => (
                    <Badge key={role.id} variant="secondary">
                      {role.display_name || role.name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsAssignRoleDialogOpen(false)}
            >
              取消
            </Button>
            <Button
              onClick={handleAssignRole}
              disabled={isSubmitting || !selectedRoleName}
            >
              {isSubmitting ? '分配中...' : '分配'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 批量删除确认对话框 */}
      <AlertDialog open={isBatchDeleteDialogOpen} onOpenChange={setIsBatchDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认批量删除</AlertDialogTitle>
            <AlertDialogDescription>
              您确定要删除选中的 <strong>{selectedUsers.size}</strong> 个用户吗？
              此操作无法撤销，这些用户的所有数据将被永久删除。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBatchDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              {isSubmitting ? '删除中...' : '确认删除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
