/**
 * 权限管理页面
 * 
 * 提供权限列表展示、创建、编辑、删除等功能
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { AxiosError } from 'axios';
import {
  Plus,
  Edit,
  Trash2,
  MoreHorizontal,
  RefreshCw,
  Key,
  Search,
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
import { Label } from '@/components/ui/label';
import { permissionsApi } from '@/lib/api/permissions';
import { useToast } from '@/lib/hooks/use-toast';
import { formatDateTime } from '@/lib/utils';
import type { Permission, CreatePermissionRequest, UpdatePermissionRequest } from '@/types';

export default function PermissionsPage() {
  const { toast } = useToast();

  // 状态管理
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [filteredPermissions, setFilteredPermissions] = useState<Permission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // 对话框状态
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedPermission, setSelectedPermission] = useState<Permission | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 表单状态
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });

  /** 加载权限列表 */
  const loadPermissions = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await permissionsApi.getPermissions();
      setPermissions(response || []);
      setFilteredPermissions(response || []);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: '加载失败',
        description: '无法加载权限列表，请稍后重试',
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadPermissions();
  }, [loadPermissions]);

  /** 搜索过滤 */
  useEffect(() => {
    if (!searchQuery) {
      setFilteredPermissions(permissions);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = permissions.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          (p.description && p.description.toLowerCase().includes(query))
      );
      setFilteredPermissions(filtered);
    }
  }, [searchQuery, permissions]);

  /** 重置表单 */
  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
    });
  };

  /** 打开创建对话框 */
  const openCreateDialog = () => {
    resetForm();
    setIsCreateDialogOpen(true);
  };

  /** 打开编辑对话框 */
  const openEditDialog = (permission: Permission) => {
    setSelectedPermission(permission);
    setFormData({
      name: permission.name,
      description: permission.description || '',
    });
    setIsEditDialogOpen(true);
  };

  /** 打开删除确认对话框 */
  const openDeleteDialog = (permission: Permission) => {
    setSelectedPermission(permission);
    setIsDeleteDialogOpen(true);
  };

  /** 创建权限 */
  const handleCreatePermission = async () => {
    if (!formData.name) {
      toast({
        variant: 'destructive',
        title: '验证失败',
        description: '请输入权限名称',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const data: CreatePermissionRequest = {
        name: formData.name,
        description: formData.description || undefined,
      };

      await permissionsApi.createPermission(data);
      toast({
        title: '创建成功',
        description: `权限 ${formData.name} 已成功创建`,
      });
      setIsCreateDialogOpen(false);
      loadPermissions();
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '创建失败',
        description: axiosError.response?.data?.detail || '无法创建权限',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 更新权限 */
  const handleUpdatePermission = async () => {
    if (!selectedPermission) return;

    setIsSubmitting(true);
    try {
      const data: UpdatePermissionRequest = {
        name: formData.name || undefined,
        description: formData.description || undefined,
      };

      await permissionsApi.updatePermission(selectedPermission.id, data);
      toast({
        title: '更新成功',
        description: '权限信息已更新',
      });
      setIsEditDialogOpen(false);
      loadPermissions();
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '更新失败',
        description: axiosError.response?.data?.detail || '无法更新权限',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 删除权限 */
  const handleDeletePermission = async () => {
    if (!selectedPermission) return;

    setIsSubmitting(true);
    try {
      await permissionsApi.deletePermission(selectedPermission.id);
      toast({
        title: '删除成功',
        description: `权限 ${selectedPermission.name} 已被删除`,
      });
      setIsDeleteDialogOpen(false);
      loadPermissions();
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '删除失败',
        description: axiosError.response?.data?.detail || '无法删除权限',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 解析权限名称获取资源和操作 */
  const parsePermissionName = (name: string) => {
    const parts = name.split(':');
    if (parts.length === 2) {
      return { resource: parts[0], action: parts[1] };
    }
    return { resource: name, action: '' };
  };

  /** 获取操作类型的颜色 */
  const getActionBadgeVariant = (action: string): 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' => {
    switch (action.toLowerCase()) {
      case 'read':
      case 'view':
        return 'secondary';
      case 'create':
      case 'write':
        return 'success';
      case 'update':
      case 'edit':
        return 'warning';
      case 'delete':
      case 'remove':
        return 'destructive';
      default:
        return 'default';
    }
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">权限管理</h1>
          <p className="text-slate-500 mt-1">管理系统中的所有权限定义</p>
        </div>
        <Button onClick={openCreateDialog} className="gap-2">
          <Plus className="h-4 w-4" />
          新建权限
        </Button>
      </div>

      {/* 搜索 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                type="search"
                placeholder="搜索权限名称或描述..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              variant="outline"
              onClick={() => setSearchQuery('')}
              disabled={!searchQuery}
            >
              清除
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={loadPermissions}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 权限列表 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium">
            权限列表
            <span className="ml-2 text-sm font-normal text-slate-500">
              共 {filteredPermissions.length} 个权限
              {searchQuery && ` (已筛选)`}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>权限名称</TableHead>
                <TableHead>资源</TableHead>
                <TableHead>操作</TableHead>
                <TableHead>描述</TableHead>
                <TableHead>创建时间</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-10">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto text-slate-400" />
                    <p className="mt-2 text-sm text-slate-500">加载中...</p>
                  </TableCell>
                </TableRow>
              ) : filteredPermissions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-10">
                    <p className="text-sm text-slate-500">
                      {searchQuery ? '没有找到匹配的权限' : '暂无权限数据'}
                    </p>
                  </TableCell>
                </TableRow>
              ) : (
                filteredPermissions.map((permission) => {
                  const { resource, action } = parsePermissionName(permission.name);
                  return (
                    <TableRow key={permission.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Key className="h-4 w-4 text-slate-400" />
                          <code className="px-2 py-0.5 bg-slate-100 rounded text-sm">
                            {permission.name}
                          </code>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{resource}</Badge>
                      </TableCell>
                      <TableCell>
                        {action && (
                          <Badge variant={getActionBadgeVariant(action)}>
                            {action}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-slate-500 max-w-xs truncate">
                        {permission.description || '暂无描述'}
                      </TableCell>
                      <TableCell className="text-slate-500">
                        {formatDateTime(permission.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEditDialog(permission)}>
                              <Edit className="mr-2 h-4 w-4" />
                              编辑
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => openDeleteDialog(permission)}
                              className="text-red-600 focus:text-red-600 focus:bg-red-50"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              删除
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 权限命名规范提示 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium">权限命名规范</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-slate-600 space-y-2">
            <p>
              推荐使用 <code className="px-1.5 py-0.5 bg-slate-100 rounded">资源:操作</code> 的格式命名权限，例如：
            </p>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>
                <code className="px-1.5 py-0.5 bg-slate-100 rounded">user:read</code> - 读取用户信息
              </li>
              <li>
                <code className="px-1.5 py-0.5 bg-slate-100 rounded">user:create</code> - 创建用户
              </li>
              <li>
                <code className="px-1.5 py-0.5 bg-slate-100 rounded">role:delete</code> - 删除角色
              </li>
              <li>
                <code className="px-1.5 py-0.5 bg-slate-100 rounded">permission:update</code> - 更新权限
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* 创建权限对话框 */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              新建权限
            </DialogTitle>
            <DialogDescription>创建一个新的系统权限</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="create-name">权限名称 *</Label>
              <Input
                id="create-name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="例如：user:read"
              />
              <p className="text-xs text-slate-500">
                建议使用 资源:操作 的格式
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-description">描述</Label>
              <Input
                id="create-description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="请输入权限描述"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsCreateDialogOpen(false)}
            >
              取消
            </Button>
            <Button onClick={handleCreatePermission} disabled={isSubmitting}>
              {isSubmitting ? '创建中...' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑权限对话框 */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Edit className="h-5 w-5" />
              编辑权限
            </DialogTitle>
            <DialogDescription>
              修改权限 {selectedPermission?.name} 的信息
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">权限名称</Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="例如：user:read"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-description">描述</Label>
              <Input
                id="edit-description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="请输入权限描述"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleUpdatePermission} disabled={isSubmitting}>
              {isSubmitting ? '保存中...' : '保存'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除权限</AlertDialogTitle>
            <AlertDialogDescription>
              您确定要删除权限 <strong>{selectedPermission?.name}</strong> 吗？
              此操作无法撤销，所有分配了此权限的角色将失去该权限。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeletePermission}
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
