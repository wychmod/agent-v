from typing import Any


class AppException(RuntimeError):
    """基础应用异常类

    所有应用层异常的基类，继承自RuntimeError。
    提供统一的错误码、HTTP状态码、错误消息和附加数据的封装。

    Attributes:
        code: 业务错误码，用于前端识别错误类型
        status_code: HTTP状态码，符合RESTful规范
        message: 错误描述信息，面向用户友好
        data: 附加错误数据，如字段校验失败详情

    Example:
        >>> raise AppException(
        ...     code=1001,
        ...     status_code=400,
        ...     message="自定义错误",
        ...     data={"field": "username"}
        ... )
    """

    def __init__(
        self,
        *,
        code: int = 400,
        status_code: int = 400,
        message: str = "应用发生错误，请稍后重试",
        data: Any = None,
    ):
        self.code = code
        self.status_code = status_code
        self.message = message
        self.data = data
        super().__init__(message)

    def __str__(self) -> str:
        """返回格式化的错误字符串"""
        if self.data:
            return f"[{self.code}] {self.message} (data: {self.data})"
        return f"[{self.code}] {self.message}"

    def __repr__(self) -> str:
        """返回异常对象的详细表示"""
        return (
            f"{self.__class__.__name__}("
            f"code={self.code}, "
            f"status_code={self.status_code}, "
            f"message={self.message!r}, "
            f"data={self.data!r}"
            f")"
        )

    def to_dict(self) -> dict[str, Any]:
        """将异常转换为字典格式，便于序列化为JSON响应

        Returns:
            包含错误信息的字典，结构如下：
            {
                "code": 业务错误码,
                "message": 错误描述,
                "data": 附加数据 (可选)
            }
        """
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.data is not None:
            result["data"] = self.data
        return result


# ==================== 4xx 客户端错误 ====================


class ClientError(AppException):
    """客户端错误基类 (4xx)

    表示由于客户端请求存在问题而导致的错误，
    如参数错误、认证失败、资源不存在等。
    """

    def __init__(
        self,
        *,
        code: int = 400,
        status_code: int = 400,
        message: str = "请求错误",
        data: Any = None,
    ):
        super().__init__(
            code=code,
            status_code=status_code,
            message=message,
            data=data,
        )


class BadRequestError(ClientError):
    """请求参数错误 (400)

    服务器无法理解客户端的请求，通常由于语法错误或缺少必需参数。

    Example:
        >>> raise BadRequestError("缺少必需的参数: user_id")
        >>> raise BadRequestError(message="JSON格式不正确")
    """

    def __init__(
        self, message: str = "请求参数错误，请检查后重试", *, data: Any = None
    ):
        super().__init__(status_code=400, code=400, message=message, data=data)


class UnauthorizedError(ClientError):
    """未认证错误 (401)

    请求需要用户身份验证，但客户端未提供有效的认证凭据。

    Example:
        >>> raise UnauthorizedError("Token已过期")
        >>> raise UnauthorizedError("缺少Authorization头")
    """

    def __init__(self, message: str = "未授权访问，请先登录", *, data: Any = None):
        super().__init__(status_code=401, code=401, message=message, data=data)


class ForbiddenError(ClientError):
    """禁止访问错误 (403)

    服务器理解请求但拒绝授权，通常由于权限不足。

    Example:
        >>> raise ForbiddenError("您没有权限访问此资源")
        >>> raise ForbiddenError(resource="订单", action="删除")
    """

    def __init__(
        self,
        message: str = "禁止访问，权限不足",
        *,
        resource: str | None = None,
        action: str | None = None,
        data: Any = None,
    ):
        # 如果提供了resource和action，构建更详细的错误信息
        if resource and action:
            message = f"您没有权限{action}该{resource}"
        super().__init__(status_code=403, code=403, message=message, data=data)


class NotFoundError(ClientError):
    """资源未找到错误 (404)

    服务器找不到请求的资源，通常由于资源不存在或已被删除。

    Example:
        >>> raise NotFoundError(resource="用户", identifier="user_123")
        >>> raise NotFoundError(message="指定的文章不存在")
    """

    def __init__(
        self,
        message: str = "请求的资源不存在",
        *,
        resource: str | None = None,
        identifier: str | None = None,
        data: Any = None,
    ):
        # 如果提供了resource和identifier，构建更详细的错误信息
        if resource and identifier:
            message = f"未找到指定的{resource}: {identifier}"
        elif resource:
            message = f"未找到指定的{resource}"
        super().__init__(status_code=404, code=404, message=message, data=data)


class ConflictError(ClientError):
    """资源冲突错误 (409)

    请求与服务器当前状态冲突，通常由于资源已存在或状态不允许。

    Example:
        >>> raise ConflictError(resource="用户", reason="邮箱已被注册")
        >>> raise ConflictError(message="该订单状态不允许修改")
    """

    def __init__(
        self,
        message: str = "资源冲突，请求无法完成",
        *,
        resource: str | None = None,
        reason: str | None = None,
        data: Any = None,
    ):
        if resource and reason:
            message = f"{resource}{reason}"
        super().__init__(status_code=409, code=409, message=message, data=data)


class UnprocessableError(ClientError):
    """无法处理的实体错误 (422)

    服务器理解请求实体的内容类型，但包含语义错误，
    如业务规则验证失败。

    Example:
        >>> raise UnprocessableError(field="age", reason="年龄必须大于18岁")
        >>> raise UnprocessableError(message="账户余额不足")
    """

    def __init__(
        self,
        message: str = "请求数据验证失败",
        *,
        field: str | None = None,
        reason: str | None = None,
        data: Any = None,
    ):
        if field and reason:
            message = f"{field}: {reason}"
        super().__init__(status_code=422, code=422, message=message, data=data)


class ValidationError(UnprocessableError):
    """数据校验错误 (422)

    请求参数格式不正确或缺少必需字段。
    这是UnprocessableError的别名，提供更直观的命名。

    Example:
        >>> raise ValidationError(field="email", reason="邮箱格式不正确")
        >>> raise ValidationError(message="请求体必须是有效的JSON")
    """

    def __init__(
        self,
        message: str = "请求参数数据校验错误",
        *,
        field: str | None = None,
        reason: str | None = None,
        errors: list[dict] | None = None,
    ):
        # errors用于存储多个字段的校验错误
        data = {"errors": errors} if errors else None
        super().__init__(message=message, field=field, reason=reason, data=data)


class TooManyRequestsError(ClientError):
    """请求过多错误 (429)

    客户端在特定时间内发送了太多请求，触发了限流保护。

    Example:
        >>> raise TooManyRequestsError(retry_after=60)
        >>> raise TooManyRequestsError("API调用次数已超限")
    """

    def __init__(
        self,
        message: str = "请求过多，触发限流，请稍后重试",
        *,
        retry_after: int | None = None,
        data: Any = None,
    ):
        # 合并retry_after到data中
        merged_data = data or {}
        if retry_after is not None:
            if isinstance(merged_data, dict):
                merged_data["retry_after"] = retry_after
            else:
                merged_data = {"retry_after": retry_after, "extra": merged_data}
        super().__init__(
            status_code=429,
            code=429,
            message=message,
            data=merged_data if merged_data else None,
        )


# ==================== 5xx 服务端错误 ====================


class ServerError(AppException):
    """服务端错误基类 (5xx)

    表示服务器在处理请求时发生了内部错误，
    这类错误通常需要服务端开发人员介入处理。
    """

    def __init__(
        self,
        *,
        code: int = 500,
        status_code: int = 500,
        message: str = "服务器内部错误",
        data: Any = None,
    ):
        super().__init__(
            code=code,
            status_code=status_code,
            message=message,
            data=data,
        )


class ServerInternalError(ServerError):
    """服务器内部错误 (500)

    服务器遇到了意外情况，无法完成请求。
    通常由于代码缺陷或不可预期的运行时错误。

    Example:
        >>> raise ServerInternalError("数据库连接失败")
        >>> raise ServerInternalError("第三方服务响应异常")
    """

    def __init__(
        self, message: str = "服务器出现异常，请稍后重试", *, data: Any = None
    ):
        super().__init__(status_code=500, code=500, message=message, data=data)


class ServiceUnavailableError(ServerError):
    """服务不可用错误 (503)

    服务器暂时无法处理请求，通常由于过载或维护。

    Example:
        >>> raise ServiceUnavailableError("数据库维护中")
        >>> raise ServiceUnavailableError(retry_after=300)
    """

    def __init__(
        self,
        message: str = "服务暂时不可用，请稍后重试",
        *,
        retry_after: int | None = None,
        data: Any = None,
    ):
        merged_data = data or {}
        if retry_after is not None:
            if isinstance(merged_data, dict):
                merged_data["retry_after"] = retry_after
            else:
                merged_data = {"retry_after": retry_after, "extra": merged_data}
        super().__init__(
            status_code=503,
            code=503,
            message=message,
            data=merged_data if merged_data else None,
        )


# 保持向后兼容的别名
ServerRequestsError = ServerInternalError
