"""健康状态领域模型模块

本模块定义系统健康检查的状态模型。

用于表示各依赖服务（如数据库、缓存）的运行状态，
支持健康检查接口返回统一格式的状态信息。
"""

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """健康状态模型

    表示单个服务的健康检查结果。

    Attributes:
        service: 服务名称（如 mysql、redis）
        status: 状态值（ok=正常, error=异常）
        details: 状态详情，异常时包含错误信息
    """

    service: str = Field(default="", description="健康检查对应的服务名字")
    status: str = Field(
        default="", description="健康检查状态，支持ok表示正常, error表示出错"
    )
    details: str = Field(default="", description="出错时的详情提示")
