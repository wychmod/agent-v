/**
 * 角色管理页面
 * 
 * 提供角色列表展示、创建、编辑、删除、权限分配等功能
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { AxiosError } from 'axios';
import {
  Plus,
  Edit,
  Trash2,
  Key,
  MoreHorizontal,
  RefreshCw,
  Shield,
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
import { rolesApi } from '@/lib/api/roles';
import { permissionsApi } from '@/lib/api/permissions';
import { useToast } from '@/lib/hooks/use-toast';
import { formatDateTime } from '@/lib/utils';
import type { Role, Permission, CreateRoleRequest, UpdateRoleRequest } from '@/types';

export default function RolesPage() {
  const { toast } = useToast();

  // 状态管理
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // 对话框状态
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isPermissionDialogOpen, setIsPermissionDialogOpen] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [rolePermissions, setRolePermissions] = useState<Permission[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 表单状态
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });
  const [selectedPermissionId, setSelectedPermissionId] = useState('');

  /** 加载角色列表 */
  const loadRoles = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await rolesApi.getRoles();
      setRoles(response || []);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: '加载失败',
        description: '无法加载角色列表，请稍后重试',
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  /** 加载权限列表 */
  const loadPermissions = async () => {
    try {
      const response = await permissionsApi.getPermissions();
      setPermissions(response || []);
    } catch (error) {
      console.error('加载权限列表失败:', error);
    }
  };

  /** 加载角色的权限 */
  const loadRolePermissions = async (roleId: string) => {
    try {
      const response = await rolesApi.getRolePermissions(roleId);
      setRolePermissions(response || []);
    } catch (error) {
      console.error('加载角色权限失败:', error);
      setRolePermissions([]);
    }
  };

  useEffect(() => {
    loadRoles();
    loadPermissions();
  }, [loadRoles]);

  /** 重置表单 */
  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
    });
    setSelectedPermissionId('');
  };

  /** 打开创建对话框 */
  const openCreateDialog = () => {
    resetForm();
    setIsCreateDialogOpen(true);
  };

  /** 打开编辑对话框 */
  const openEditDialog = (role: Role) => {
    setSelectedRole(role);
    setFormData({
      name: role.name,
      description: role.description || '',
    });
    setIsEditDialogOpen(true);
  };

  /** 打开删除确认对话框 */
  const openDeleteDialog = (role: Role) => {
    setSelectedRole(role);
    setIsDeleteDialogOpen(true);
  };

  /** 打开权限管理对话框 */
  const openPermissionDialog = async (role: Role) => {
    setSelectedRole(role);
    setSelectedPermissionId('');
    await loadRolePermissions(role.id);
    setIsPermissionDialogOpen(true);
  };

  /** 创建角色 */
  const handleCreateRole = async () => {
    if (!formData.name) {
      toast({
        variant: 'destructive',
        title: '验证失败',
        description: '请输入角色名称',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const data: CreateRoleRequest = {
        name: formData.name,
        description: formData.description || undefined,
      };

      await rolesApi.createRole(data);
      toast({
        title: '创建成功',
        description: `角色 ${formData.name} 已成功创建`,
      });
      setIsCreateDialogOpen(false);
      loadRoles();
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '创建失败',
        description: axiosError.response?.data?.detail || '无法创建角色',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 更新角色 */
  const handleUpdateRole = async () => {
    if (!selectedRole) return;

    setIsSubmitting(true);
    try {
      const data: UpdateRoleRequest = {
        name: formData.name || undefined,
        description: formData.description || undefined,
      };

      await rolesApi.updateRole(selectedRole.id, data);
      toast({
        title: '更新成功',
        description: '角色信息已更新',
      });
      setIsEditDialogOpen(false);
      loadRoles();
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '更新失败',
        description: axiosError.response?.data?.detail || '无法更新角色',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 删除角色 */
  const handleDeleteRole = async () => {
    if (!selectedRole) return;

    setIsSubmitting(true);
    try {
      await rolesApi.deleteRole(selectedRole.id);
      toast({
        title: '删除成功',
        description: `角色 ${selectedRole.name} 已被删除`,
      });
      setIsDeleteDialogOpen(false);
      loadRoles();
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '删除失败',
        description: axiosError.response?.data?.detail || '无法删除角色',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 分配权限 */
  const handleAssignPermission = async () => {
    if (!selectedRole || !selectedPermissionId) return;

    setIsSubmitting(true);
    try {
      await rolesApi.assignPermission(selectedRole.id, selectedPermissionId);
      toast({
        title: '分配成功',
        description: '权限已成功分配给角色',
      });
      await loadRolePermissions(selectedRole.id);
      setSelectedPermissionId('');
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '分配失败',
        description: axiosError.response?.data?.detail || '无法分配权限',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /** 移除权限 */
  const handleRemovePermission = async (permissionId: string) => {
    if (!selectedRole) return;

    try {
      await rolesApi.removePermission(selectedRole.id, permissionId);
      toast({
        title: '移除成功',
        description: '权限已从角色移除',
      });
      await loadRolePermissions(selectedRole.id);
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      toast({
        variant: 'destructive',
        title: '移除失败',
        description: axiosError.response?.data?.detail || '无法移除权限',
      });
    }
  };

  /** 检查是否为系统角色 */
  const isSystemRole = (roleName: string) => {
    return ['admin', 'user'].includes(roleName.toLowerCase());
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">角色管理</h1>
          <p className="text-slate-500 mt-1">管理系统中的用户角色和权限</p>
        </div>
        <Button onClick={openCreateDialog} className="gap-2">
          <Plus className="h-4 w-4" />
          新建角色
        </Button>
      </div>

      {/* 角色列表 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-base font-medium">
            角色列表
            <span className="ml-2 text-sm font-normal text-slate-500">
              共 {roles.length} 个角色
            </span>
          </CardTitle>
          <Button
            variant="ghost"
            size="icon"
            onClick={loadRoles}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>角色名称</TableHead>
                <TableHead>描述</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>创建时间</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-10">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto text-slate-400" />
                    <p className="mt-2 text-sm text-slate-500">加载中...</p>
                  </TableCell>
                </TableRow>
              ) : roles.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-10">
                    <p className="text-sm text-slate-500">暂无角色数据</p>
                  </TableCell>
                </TableRow>
              ) : (
                roles.map((role) => (
                  <TableRow key={role.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-slate-400" />
                        <span className="font-medium">{role.name}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-500">
                      {role.description || '暂无描述'}
                    </TableCell>
                    <TableCell>
                      {isSystemRole(role.name) ? (
                        <Badge variant="secondary">系统角色</Badge>
                      ) : (
                        <Badge variant="outline">自定义</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-slate-500">
                      {formatDateTime(role.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openPermissionDialog(role)}>
                            <Key className="mr-2 h-4 w-4" />
                            管理权限
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openEditDialog(role)}>
                            <Edit className="mr-2 h-4 w-4" />
                            编辑
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => openDeleteDialog(role)}
                            disabled={isSystemRole(role.name)}
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
        </CardContent>
      </Card>

      {/* 创建角色对话框 */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              新建角色
            </DialogTitle>
            <DialogDescription>创建一个新的用户角色</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="create-name">角色名称 *</Label>
              <Input
                id="create-name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="请输入角色名称"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-description">描述</Label>
              <Input
                id="create-description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="请输入角色描述"
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
            <Button onClick={handleCreateRole} disabled={isSubmitting}>
              {isSubmitting ? '创建中...' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑角色对话框 */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Edit className="h-5 w-5" />
              编辑角色
            </DialogTitle>
            <DialogDescription>
              修改角色 {selectedRole?.name} 的信息
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">角色名称</Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="请输入角色名称"
                disabled={selectedRole ? isSystemRole(selectedRole.name) : false}
              />
              {selectedRole && isSystemRole(selectedRole.name) && (
                <p className="text-xs text-slate-500">系统角色名称不可修改</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-description">描述</Label>
              <Input
                id="edit-description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="请输入角色描述"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleUpdateRole} disabled={isSubmitting}>
              {isSubmitting ? '保存中...' : '保存'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除角色</AlertDialogTitle>
            <AlertDialogDescription>
              您确定要删除角色 <strong>{selectedRole?.name}</strong> 吗？
              此操作无法撤销，所有拥有此角色的用户将失去相关权限。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteRole}
              className="bg-red-600 hover:bg-red-700"
            >
              {isSubmitting ? '删除中...' : '确认删除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 权限管理对话框 */}
      <Dialog open={isPermissionDialogOpen} onOpenChange={setIsPermissionDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              管理权限
            </DialogTitle>
            <DialogDescription>
              为角色 {selectedRole?.name} 分配权限
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* 添加权限 */}
            <div className="flex items-end gap-4">
              <div className="flex-1 space-y-2">
                <Label>添加权限</Label>
                <Select value={selectedPermissionId} onValueChange={setSelectedPermissionId}>
                  <SelectTrigger>
                    <SelectValue placeholder="请选择要添加的权限" />
                  </SelectTrigger>
                  <SelectContent>
                    {permissions
                      .filter(
                        (p) => !rolePermissions.some((rp) => rp.id === p.id)
                      )
                      .map((permission) => (
                        <SelectItem key={permission.id} value={permission.id}>
                          {permission.name}
                          {permission.description && (
                            <span className="text-slate-400 ml-2">
                              - {permission.description}
                            </span>
                          )}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>
              <Button
                onClick={handleAssignPermission}
                disabled={isSubmitting || !selectedPermissionId}
              >
                添加
              </Button>
            </div>

            {/* 已有权限列表 */}
            <div className="space-y-2">
              <Label>当前权限 ({rolePermissions.length})</Label>
              <div className="border rounded-lg divide-y max-h-60 overflow-y-auto">
                {rolePermissions.length === 0 ? (
                  <p className="text-sm text-slate-500 p-4 text-center">
                    该角色暂无权限
                  </p>
                ) : (
                  rolePermissions.map((permission) => (
                    <div
                      key={permission.id}
                      className="flex items-center justify-between p-3 hover:bg-slate-50"
                    >
                      <div>
                        <p className="font-medium text-sm">{permission.name}</p>
                        {permission.description && (
                          <p className="text-xs text-slate-500">
                            {permission.description}
                          </p>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemovePermission(permission.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsPermissionDialogOpen(false)}
            >
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
