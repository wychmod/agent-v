"""SQLAlchemy ORM 基础模型模块

本模块定义所有数据库模型的基类。

使用方式:
    from app.infrastructure.models.base import Base

    class MyModel(Base):
        __tablename__ = "my_table"
        # 定义字段...

Note:
    所有 ORM 模型都必须继承此 Base 类，
    以确保 SQLAlchemy 能够正确管理表映射和关系。
"""

from sqlalchemy.orm import declarative_base

# 定义基础 ORM 类，所有数据库模型都需要继承这个类
# declarative_base() 创建一个基类，用于声明式模型定义
Base = declarative_base()
