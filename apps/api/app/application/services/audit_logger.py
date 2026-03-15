"""审计日志服务 - 提供优雅的审计日志记录方式

本模块提供三种审计日志记录方式:
1. 装饰器 @audit_log - 自动记录函数执行
2. 简化 API AuditLogger.log() - 一行代码记录日志
3. 上下文管理器 audit_context() - 简化复杂流程的日志记录

使用示例:
    # 方式1: 装饰器
    @audit_log(action="create_user", resource="user")
    async def create_user(self, ...):
        ...

    # 方式2: 简化API
    await AuditLogger.log(
        audit_repo=audit_repo,
        action="login",
        resource="user",
        user_id=user_id,
    )

    # 方式3: 上下文管理器
    async with audit_context(audit_repo, "update", "user", user_id) as ctx:
        await ctx.success(details={"updated_fields": [...]})
"""

import functools
import inspect
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from app.domain.models.user import AuditLog, User
from app.domain.repositories.audit_log_repository import AuditLogRepository

logger = logging.getLogger(__name__)

# 上下文变量，用于在服务方法间传递审计日志上下文
_audit_context: ContextVar["AuditContextData | None"] = ContextVar(
    "audit_context", default=None
)


class AuditAction:
    """预定义的操作类型常量，避免字符串拼写错误"""

    # 认证相关
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    REFRESH_TOKEN = "refresh_token"
    VERIFY_EMAIL = "verify_email"
    REQUEST_PASSWORD_RESET = "request_password_reset"
    RESET_PASSWORD = "reset_password"
    CHANGE_PASSWORD = "change_password"

    # 用户管理
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    UPDATE_PROFILE = "update_profile"
    ADMIN_CREATE_USER = "admin_create_user"
    ADMIN_UPDATE_USER = "admin_update_user"

    # 角色管理
    CREATE_ROLE = "create_role"
    UPDATE_ROLE = "update_role"
    DELETE_ROLE = "delete_role"
    ASSIGN_ROLE = "assign_role"
    REMOVE_ROLE = "remove_role"

    # 权限管理
    CREATE_PERMISSION = "create_permission"
    UPDATE_PERMISSION = "update_permission"
    DELETE_PERMISSION = "delete_permission"
    ASSIGN_PERMISSION = "assign_permission"
    REMOVE_PERMISSION = "remove_permission"


class AuditResource:
    """预定义的资源类型常量"""

    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    SYSTEM = "system"


class AuditStatus:
    """预定义的状态常量"""

    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class AuditContextData:
    """审计日志上下文数据"""

    user_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    current_user: User | None = None


class AuditLogger:
    """审计日志记录器 - 简化API

    提供静态方法用于快速记录审计日志，自动从上下文获取用户信息。
    """

    @staticmethod
    def get_context() -> AuditContextData | None:
        """获取当前审计日志上下文"""
        return _audit_context.get()

    @staticmethod
    def set_context(
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        current_user: User | None = None,
    ) -> None:
        """设置审计日志上下文"""
        _audit_context.set(
            AuditContextData(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                current_user=current_user,
            )
        )

    @staticmethod
    def clear_context() -> None:
        """清除审计日志上下文"""
        _audit_context.set(None)

    @staticmethod
    async def log(
        audit_repo: AuditLogRepository,
        action: str,
        resource: str,
        user_id: str | None = None,
        resource_id: str | None = None,
        status: str = "success",
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog | None:
        """记录审计日志 - 简化API

        自动从上下文获取用户信息，只需提供必要参数即可记录日志。

        Args:
            audit_repo: 审计日志仓储
            action: 操作类型
            resource: 资源类型
            user_id: 用户ID（可选，默认从上下文获取）
            resource_id: 资源ID（可选）
            status: 操作状态，默认"success"
            details: 操作详情（可选）
            ip_address: IP地址（可选，默认从上下文获取）
            user_agent: 用户代理（可选，默认从上下文获取）

        Returns:
            创建的审计日志对象，或None（如果记录失败）
        """
        try:
            # 从上下文获取默认值
            ctx = _audit_context.get()
            if ctx:
                user_id = (
                    user_id
                    or ctx.user_id
                    or (ctx.current_user.id if ctx.current_user else None)
                )
                ip_address = ip_address or ctx.ip_address
                user_agent = user_agent or ctx.user_agent

            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                details=details,
            )
            result = await audit_repo.create(audit_log)
            logger.debug(f"审计日志记录成功: {action} on {resource}")
            return result
        except Exception as e:
            logger.error(f"审计日志记录失败: {e}")
            return None

    @staticmethod
    async def log_success(
        audit_repo: AuditLogRepository,
        action: str,
        resource: str,
        resource_id: str | None = None,
        details: dict | None = None,
        **kwargs,
    ) -> AuditLog | None:
        """记录成功操作的审计日志"""
        return await AuditLogger.log(
            audit_repo=audit_repo,
            action=action,
            resource=resource,
            resource_id=resource_id,
            status="success",
            details=details,
            **kwargs,
        )

    @staticmethod
    async def log_failure(
        audit_repo: AuditLogRepository,
        action: str,
        resource: str,
        resource_id: str | None = None,
        details: dict | None = None,
        **kwargs,
    ) -> AuditLog | None:
        """记录失败操作的审计日志"""
        return await AuditLogger.log(
            audit_repo=audit_repo,
            action=action,
            resource=resource,
            resource_id=resource_id,
            status="failed",
            details=details,
            **kwargs,
        )


def audit_log(
    action: str,
    resource: str,
    *,
    get_user_id: Callable[..., str | None] | str | None = None,
    get_resource_id: Callable[..., str | None] | str | None = None,
    get_details: Callable[..., dict | None] | None = None,
    log_on_success: bool = True,
    log_on_failure: bool = True,
) -> Callable:
    """审计日志装饰器

    自动记录函数的执行结果作为审计日志，支持成功和失败两种情况。

    Args:
        action: 操作类型，如 "create_user", "login"
        resource: 资源类型，如 "user", "role"
        get_user_id: 获取用户ID的方式：
            - 字符串: 从函数参数中获取，如 "current_user.id"
            - 可调用对象: 接收函数参数，返回用户ID
            - None: 自动从上下文获取
        get_resource_id: 获取资源ID的方式，同 get_user_id
        get_details: 获取操作详情的可调用对象
        log_on_success: 成功时是否记录日志
        log_on_failure: 失败时是否记录日志

    使用示例:
        @audit_log(action="create_user", resource="user", get_user_id="current_user.id")
        async def create_user(self, ..., current_user: User):
            ...

        @audit_log(
            action="delete_user",
            resource="user",
            get_user_id="current_user.id",
            get_resource_id="user_id",
        )
        async def delete_user(self, user_id: str, ..., current_user: User):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 获取 audit_repo 实例（假设是第一个参数或关键字参数）
            audit_repo = _extract_audit_repo(args, kwargs)
            if audit_repo is None:
                logger.warning(f"无法获取 audit_repo，跳过审计日志: {func.__name__}")
                return await func(*args, **kwargs)

            # 绑定参数
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # 提取用户信息
            user_id = _extract_value(get_user_id, bound)
            resource_id = _extract_value(get_resource_id, bound)

            # 设置上下文
            ctx_token = None
            try:
                current_user = bound.arguments.get("current_user")
                ip_address = bound.arguments.get("ip_address")
                user_agent = bound.arguments.get("user_agent")

                ctx = AuditContextData(
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    current_user=current_user,
                )
                ctx_token = _audit_context.set(ctx)

                # 执行函数
                result = await func(*args, **kwargs)

                # 记录成功日志
                if log_on_success:
                    details = _extract_details(get_details, bound, result, None)
                    await AuditLogger.log_success(
                        audit_repo=audit_repo,
                        action=action,
                        resource=resource,
                        resource_id=resource_id,
                        details=details,
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )

                return result

            except Exception as e:
                # 记录失败日志
                if log_on_failure:
                    details = _extract_details(get_details, bound, None, e)
                    details = details or {}
                    details["error"] = str(e)

                    await AuditLogger.log_failure(
                        audit_repo=audit_repo,
                        action=action,
                        resource=resource,
                        resource_id=resource_id,
                        details=details,
                        user_id=user_id,
                        ip_address=bound.arguments.get("ip_address"),
                        user_agent=bound.arguments.get("user_agent"),
                    )
                raise
            finally:
                if ctx_token:
                    _audit_context.reset(ctx_token)

        return async_wrapper

    return decorator


@asynccontextmanager
async def audit_context(
    audit_repo: AuditLogRepository,
    action: str,
    resource: str,
    user_id: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
):
    """审计日志上下文管理器

    用于在复杂业务流程中记录审计日志，支持手动标记成功或失败。

    Args:
        audit_repo: 审计日志仓储
        action: 操作类型
        resource: 资源类型
        user_id: 用户ID（可选，默认从上下文获取）
        resource_id: 资源ID（可选）
        ip_address: IP地址（可选）
        user_agent: 用户代理（可选）

    使用示例:
        async with audit_context(
            audit_repo, "complex_operation", "system", user_id
        ) as ctx:
            # 执行业务逻辑
            result = await do_something()
            # 标记成功并记录详情
            await ctx.success(details={"result": result})
    """
    ctx = _AuditContext(
        audit_repo=audit_repo,
        action=action,
        resource=resource,
        user_id=user_id,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    try:
        yield ctx
        # 如果没有显式调用 success 或 failure，默认记录成功
        if not ctx._recorded:
            await ctx.success()
    except Exception as e:
        if not ctx._recorded:
            await ctx.failure(str(e))
        raise


class _AuditContext:
    """审计日志上下文对象"""

    def __init__(
        self,
        audit_repo: AuditLogRepository,
        action: str,
        resource: str,
        user_id: str | None,
        resource_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ):
        self._audit_repo = audit_repo
        self._action = action
        self._resource = resource
        self._user_id = user_id
        self._resource_id = resource_id
        self._ip_address = ip_address
        self._user_agent = user_agent
        self._recorded = False

    async def success(self, details: dict | None = None) -> None:
        """记录成功状态"""
        if not self._recorded:
            await AuditLogger.log_success(
                audit_repo=self._audit_repo,
                action=self._action,
                resource=self._resource,
                resource_id=self._resource_id,
                details=details,
                user_id=self._user_id,
                ip_address=self._ip_address,
                user_agent=self._user_agent,
            )
            self._recorded = True

    async def failure(self, reason: str, details: dict | None = None) -> None:
        """记录失败状态"""
        if not self._recorded:
            details = details or {}
            details["error"] = reason
            await AuditLogger.log_failure(
                audit_repo=self._audit_repo,
                action=self._action,
                resource=self._resource,
                resource_id=self._resource_id,
                details=details,
                user_id=self._user_id,
                ip_address=self._ip_address,
                user_agent=self._user_agent,
            )
            self._recorded = True


def _extract_audit_repo(args: tuple, kwargs: dict) -> AuditLogRepository | None:
    """从参数中提取 audit_repo"""
    # 尝试从 kwargs 获取
    if "audit_repo" in kwargs:
        return kwargs["audit_repo"]
    if "audit_log_repository" in kwargs:
        return kwargs["audit_log_repository"]

    # 尝试从 args 获取（假设是 self._audit_repo）
    if args and hasattr(args[0], "_audit_repo"):
        return args[0]._audit_repo

    return None


def _extract_value(
    extractor: Callable[..., str | None] | str | None,
    bound: inspect.BoundArguments,
) -> str | None:
    """从绑定参数中提取值"""
    if extractor is None:
        return None

    if callable(extractor):
        return extractor(bound.arguments)

    if isinstance(extractor, str):
        # 支持点号访问，如 "current_user.id"
        parts = extractor.split(".")
        value = bound.arguments.get(parts[0])
        for part in parts[1:]:
            if value is None:
                break
            value = getattr(value, part, None)
        return value

    return None


def _extract_details(
    extractor: Callable[..., dict | None] | None,
    bound: inspect.BoundArguments,
    result: Any,
    error: Exception | None,
) -> dict | None:
    """提取操作详情"""
    if extractor is None:
        return None

    if callable(extractor):
        try:
            sig = inspect.signature(extractor)
            if len(sig.parameters) == 1:
                return extractor(bound.arguments)
            else:
                return extractor(bound.arguments, result, error)
        except Exception as e:
            logger.warning(f"提取审计日志详情失败: {e}")
            return None

    return None
