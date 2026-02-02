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

    # 数据库相关配置
    sqlalchemy_database_uri: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/manus"

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()


@lru_cache
def get_settings() -> Settings:
    """获取当前MoocManus项目的配置信息，并对内容进行缓存，避免重复读取"""
    return Settings()
