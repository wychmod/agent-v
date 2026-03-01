from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    项目配置类，自动从 .env 文件读取环境变量
    """

    # 项目基础配置
    env: str = "development"
    log_level: str = "INFO"
    app_config_filepath: str = "config.yaml"
    frontend_url: str = "http://localhost:3000"

    # 数据库相关配置
    sqlalchemy_database_uri: str = (
        "mysql+aiomysql://root:xxxxxx@117.72.218.181:3306/manus"
    )

    # Redis缓存配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    # Cos腾讯云对象存储配置
    cos_secret_id: str = ""
    cos_secret_key: str = ""
    cos_region: str = ""
    cos_scheme: str = "https"
    cos_bucket: str = ""
    cos_domain: str = ""

    # JWT 认证配置
    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_refresh_secret_key: str = "your-refresh-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # 密码策略配置
    password_min_length: int = 8

    # SMTP 邮件配置
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = "noreply@example.com"
    email_from_name: str = "User Management System"

    # Admin 后台管理密钥，用于验证管理员身份，生产环境必须修改
    admin_secret_key: str = "admin-secret-key-change-in-production"
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()


@lru_cache
def get_settings() -> Settings:
    """
    获取当前项目的配置信息
    """
    return Settings()
