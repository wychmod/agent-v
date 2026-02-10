import logging
import traceback
from typing import TypeVar

from fastapi import FastAPI, HTTPException, Request
from starlette.responses import JSONResponse

from app.application.errors.exceptions import AppException
from app.interfaces.schemas import Response

logger = logging.getLogger(__name__)

T = TypeVar("T")


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器到FastAPI应用

    将三类异常处理器注册到FastAPI应用实例，实现统一的错误响应格式。
    处理优先级：AppException > HTTPException > Exception

    Args:
        app: FastAPI应用实例
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        """处理应用层自定义异常

        捕获应用层抛出的AppException及其子类异常，记录错误日志
        并返回标准化的JSON响应。这是业务逻辑错误的主要处理入口。

        Args:
            request: FastAPI请求对象，包含请求方法和URL信息
            exc: 应用层异常实例，包含status_code、code、message等属性

        Returns:
            JSONResponse: 标准化的错误响应，结构为{code, message, data}

        Note:
            - 4xx错误记录为WARNING级别（客户端错误）
            - 5xx错误记录为ERROR级别（服务端错误）
            - 响应内容使用AppException的to_dict()方法序列化
        """
        log_message = f"{request.method} {request.url.path} - AppException[{exc.code}]: {exc.message}"

        logger.error(log_message, extra={"exception": exc.to_dict()})

        return JSONResponse(
            status_code=exc.status_code,
            content=Response(
                code=exc.code, message=exc.message, data=exc.data or {}
            ).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """处理FastAPI框架抛出的HTTP异常

        捕获FastAPI内置的HTTPException（如认证失败、请求验证失败等），
        将其转换为统一的响应格式，保持与AppException一致的接口。

        Args:
            request: FastAPI请求对象
            exc: FastAPI的HTTPException实例，包含status_code和detail属性

        Returns:
            JSONResponse: 标准化的错误响应

        Note:
            - HTTPException通常由FastAPI中间件或依赖项抛出
            - detail字段可能为字符串或字典，统一转换为字符串处理
            - 4xx错误记录为WARNING，5xx记录为ERROR
        """
        # 处理detail可能为字典的情况
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        log_message = f"{request.method} {request.url.path} - HTTPException[{exc.status_code}]: {message}"

        logger.error(log_message)

        return JSONResponse(
            status_code=exc.status_code,
            content=Response(
                code=exc.status_code, message=message, data={}
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """处理未捕获的通用异常（兜底处理器）

        捕获所有未被上述处理器捕获的异常，作为最后一道防线。
        通常表示代码缺陷或未预期的运行时错误，返回500状态码。

        Args:
            request: FastAPI请求对象
            exc: 任意异常实例

        Returns:
            JSONResponse: 500错误响应，隐藏具体错误信息（安全考虑）

        Security Note:
            - 生产环境不应向客户端暴露详细的异常堆栈信息
            - 详细错误信息仅记录到服务端日志中
            - 返回给客户端的message应为通用友好提示
        """
        # 记录完整的异常信息和堆栈跟踪
        error_trace = traceback.format_exc()
        log_message = (
            f"{request.method} {request.url.path} - "
            f"未捕获异常 [{exc.__class__.__name__}]: {str(exc)}"
        )
        logger.critical(log_message)
        logger.debug(f"异常堆栈跟踪:\n{error_trace}")

        return JSONResponse(
            status_code=500,
            content=Response(
                code=500,
                message="服务器出现异常，请稍后重试",
                data={},
            ).model_dump(),
        )
