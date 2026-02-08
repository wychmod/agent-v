import logging
import logging.config
import sys
from typing import Any

from core.config import get_settings


def setup_logging():
    """
    配置 logging 模块，设置项目日志格式和输出级别。

    """
    settings = get_settings()

    # 1. 验证日志级别
    log_level = settings.log_level.upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in valid_levels:
        log_level = "INFO"

    # 2. 根据环境定义日志格式
    if settings.env == "development":
        # 开发模式：包含更多调试信息（文件名、行号）
        log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    else:
        # 生产模式：保持简洁
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 3. 构造配置字典
    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            # 根配置
            "": {
                "handlers": ["console"],
                "level": log_level,
            },
            # 可选：对特定库进行精细控制
            # "uvicorn.error": {"level": "INFO"},
            # "sqlalchemy.engine": {"level": "WARNING"},
        },
    }

    # 4. 应用配置
    logging.config.dictConfig(logging_config)

    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成 [环境: {settings.env}, 级别: {log_level}]")
