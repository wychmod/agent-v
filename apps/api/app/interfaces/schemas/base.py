from pydantic import BaseModel


class Response[T](BaseModel):
    """
    通用响应模型
    """

    code: int = 200
    message: str = "success"
    data: T | None = None

    class Config:
        from_attributes = True

    @classmethod
    def success[T](data: T | None = None, message: str = "success") -> "Response[T]":
        """
        成功响应便捷函数
        """
        return Response(code=200, message=message, data=data if data else {})

    @classmethod
    def fail[T](
        code: int = 400, message: str = "error", data: T | None = None
    ) -> "Response[T]":
        """
        错误响应便捷函数
        """
        return Response(code=code, message=message, data=data if data else {})
