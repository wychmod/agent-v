"""应用配置管理模块

本模块提供应用程序的配置管理功能，支持从环境变量和 .env 文件加载配置。

主要功能:
- 集中管理所有应用配置项
- 支持环境变量覆盖默认值
- 自动从 .env 文件加载配置
- 使用 lru_cache 实现单例模式

配置分组:
- 项目基础配置: 环境、日志级别等
- 数据库配置: MySQL 连接信息
- 缓存配置: Redis 连接信息
- 对象存储配置: 腾讯云 COS 配置
- 认证配置: JWT 密钥和过期时间
- 邮件配置: SMTP 服务器信息
- 管理后台配置: Session 密钥

使用示例:
    from core.config import get_settings

    settings = get_settings()
    print(settings.env)  # "development" 或 "production"

安全说明:
    生产环境必须修改以下默认值:
    - jwt_secret_key
    - jwt_refresh_secret_key
    - admin_secret_key
    - smtp_password
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类

    使用 pydantic-settings 自动从环境变量和 .env 文件读取配置。
    所有配置项都有默认值，可通过环境变量覆盖。

    Attributes:
        env: 运行环境（development/production）
        log_level: 日志级别
        app_config_filepath: 应用配置文件路径
        frontend_url: 前端应用 URL
        sqlalchemy_database_uri: 数据库连接 URI
        redis_*: Redis 连接配置
        cos_*: 腾讯云 COS 配置
        jwt_*: JWT 认证配置
        password_min_length: 密码最小长度
        smtp_*: SMTP 邮件服务配置
        admin_secret_key: 管理后台 Session 密钥
    """

    # 项目基础配置
    env: str = "development"  # 运行环境
    log_level: str = "INFO"  # 日志级别
    app_config_filepath: str = "config.yaml"  # 应用配置文件路径
    frontend_url: str = "http://localhost:3000"  # 前端 URL

    # 数据库相关配置
    sqlalchemy_database_uri: str = ""  # MySQL 连接 URI

    # Redis 缓存配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    # 腾讯云对象存储配置
    cos_secret_id: str = ""
    cos_secret_key: str = ""
    cos_region: str = ""
    cos_scheme: str = "https"
    cos_bucket: str = ""
    cos_domain: str = ""

    # JWT 认证配置
    jwt_secret_key: str = (
        "your-super-secret-key-change-in-production"  # 生产环境必须修改
    )
    jwt_refresh_secret_key: str = (
        "your-refresh-secret-key-change-in-production"  # 生产环境必须修改
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15  # 访问令牌过期时间（分钟）
    jwt_refresh_token_expire_days: int = 7  # 刷新令牌过期时间（天）

    # 密码策略配置
    password_min_length: int = 8

    # SMTP 邮件配置
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = "noreply@example.com"  # 发件人地址
    email_from_name: str = "User Management System"  # 发件人显示名称

    # 管理后台配置
    admin_secret_key: str = (
        "admin-secret-key-change-in-production"  # Session 密钥，生产环境必须修改
    )

    # Pydantic Settings 配置
    model_config = SettingsConfigDict(
        env_file=".env",  # 从 .env 文件加载
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略未定义的环境变量
    )


# 全局配置实例（用于模块级访问）
settings = Settings()


@lru_cache
def get_settings() -> Settings:
    """获取应用配置单例实例

    使用 lru_cache 装饰器确保配置实例全局唯一。

    Returns:
        Settings: 应用配置实例
    """
    return Settings()
