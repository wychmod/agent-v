"""API 基础响应模型模块

本模块定义 API 的标准响应格式，提供统一的响应结构。

主要数据模型:
- Response[T]: 泛型通用响应模型

响应格式约定:
- code: HTTP 状态码，200 表示成功
- message: 响应消息描述
- data: 响应数据载荷

使用示例:
    # 成功响应
    Response.success(data=user, message="获取成功")

    # 失败响应
    Response.fail(code=404, message="用户不存在")
"""

from typing import Any

from pydantic import BaseModel, ConfigDict


class Response[T](BaseModel):
    """通用响应模型

    定义API接口的标准响应格式，使用泛型支持不同类型的数据载荷。

    Attributes:
        code (int): 响应状态码，200表示成功，其他值表示各种错误类型
        message (str): 响应消息，描述请求处理结果
        data (T | dict): 响应数据载荷，可以是任意类型或字典

    Type Parameters:
        T: 数据载荷的具体类型，支持泛型参数化
    """

    code: int = 200
    message: str = "success"
    data: T | dict[Any, Any]

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def success(data: T | None = None, message: str = "success") -> "Response[T]":
        """创建成功响应

        便捷方法用于构造成功的API响应，默认使用200状态码。

        Args:
            data (T | None): 响应数据，为None时返回空字典
            message (str): 成功消息，默认为"success"

        Returns:
            Response[T]: 成功响应对象，code为200
        """
        return Response(code=200, message=message, data=data if data else {})

    @staticmethod
    def fail(
        code: int = 400, message: str = "error", data: T | None = None
    ) -> "Response[T]":
        """创建失败响应

        便捷方法用于构造失败的API响应，支持自定义错误码和错误消息。

        Args:
            code (int): 错误状态码，默认为400（客户端错误）
            message (str): 错误消息，默认为"error"
            data (T | None): 额外的错误详情数据，为None时返回空字典

        Returns:
            Response[T]: 失败响应对象，包含自定义的错误信息
        """
        return Response(code=code, message=message, data=data if data else {})
