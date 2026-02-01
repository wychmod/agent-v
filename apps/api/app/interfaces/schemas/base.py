from typing import Never

from pydantic import BaseModel, ConfigDict


class Response[T](BaseModel):
    """
    通用响应模型
    """

    code: int = 200
    message: str = "success"
    data: T | dict[Never, Never]

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def success(data: T | None = None, message: str = "success") -> "Response[T]":
        """
        成功响应便捷函数
        """
        return Response(code=200, message=message, data=data if data else {})

    @staticmethod
    def fail(
        code: int = 400, message: str = "error", data: T | None = None
    ) -> "Response[T]":
        """
        错误响应便捷函数
        """
        return Response(code=code, message=message, data=data if data else {})
