"""认证 API 路由"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.application.services.auth_service import AuthService
from app.interfaces.dependencies.auth_dependencies import (
    get_auth_service,
    get_client_ip,
    get_current_user,
    get_user_agent,
)
from app.interfaces.schemas.auth_schemas import (
    LoginResponse,
    LoginSchema,
    LogoutSchema,
    RefreshTokenSchema,
    ResetPasswordRequestSchema,
    ResetPasswordSchema,
    TokenResponse,
    UserRegisterSchema,
    UserResponse,
    VerifyEmailSchema,
)
from app.interfaces.schemas.base import Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/register",
    response_model=Response[UserResponse],
    summary="用户注册",
    description="注册新用户，发送邮箱验证邮件",
)
async def register(
    data: UserRegisterSchema,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response[UserResponse]:
    ip_address = get_client_ip(request)
    user = await auth_service.register(
        email=data.email,
        username=data.username,
        password=data.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(
        message="注册成功，请查收邮件验证您的邮箱",
        data=UserResponse.from_user(user),
    )


@router.post(
    "/login",
    response_model=Response[LoginResponse],
    summary="用户登录",
    description="用户登录，返回访问令牌和刷新令牌",
)
async def login(
    data: LoginSchema,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response[LoginResponse]:
    ip_address = get_client_ip(request)
    result = await auth_service.login(
        email=data.email,
        password=data.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(
        message="登录成功",
        data=LoginResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
            user=UserResponse.from_user(result["user"]),
        ),
    )


@router.post(
    "/logout",
    response_model=Response,
    summary="用户登出",
    description="用户登出，使当前访问令牌和刷新令牌失效",
)
async def logout(
    request: Request,
    data: LogoutSchema,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
    _: Annotated[None, Depends(get_current_user)],
) -> Response:
    ip_address = get_client_ip(request)
    auth_header = request.headers.get("Authorization", "")
    access_token = (
        auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    )

    await auth_service.logout(
        access_token=access_token,
        refresh_token=data.refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(message="登出成功")


@router.post(
    "/refresh",
    response_model=Response[TokenResponse],
    summary="刷新令牌",
    description="使用刷新令牌获取新的访问令牌",
)
async def refresh_token(
    data: RefreshTokenSchema,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response[TokenResponse]:
    ip_address = get_client_ip(request)
    result = await auth_service.refresh_token(
        refresh_token=data.refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(
        message="令牌刷新成功",
        data=TokenResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
        ),
    )


@router.post(
    "/verify-email",
    response_model=Response,
    summary="验证邮箱",
    description="验证用户邮箱地址",
)
async def verify_email(
    data: VerifyEmailSchema,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response:
    ip_address = get_client_ip(request)
    await auth_service.verify_email(
        token=data.token,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(message="邮箱验证成功")


@router.post(
    "/reset-password-request",
    response_model=Response,
    summary="请求密码重置",
    description="发送密码重置邮件",
)
async def reset_password_request(
    data: ResetPasswordRequestSchema,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response:
    ip_address = get_client_ip(request)
    await auth_service.request_password_reset(
        email=data.email,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(message="如果该邮箱存在，重置邮件已发送")


@router.post(
    "/reset-password",
    response_model=Response,
    summary="重置密码",
    description="使用重置令牌设置新密码",
)
async def reset_password(
    data: ResetPasswordSchema,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_agent: Annotated[str | None, Depends(get_user_agent)],
) -> Response:
    ip_address = get_client_ip(request)
    await auth_service.reset_password(
        token=data.token,
        new_password=data.new_password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return Response.success(message="密码重置成功")
