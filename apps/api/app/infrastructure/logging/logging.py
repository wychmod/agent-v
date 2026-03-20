"""日志配置模块

本模块提供应用程序日志系统的初始化配置功能。

主要功能:
- 根据环境（开发/生产）配置不同的日志格式
- 支持可配置的日志级别
- 统一的控制台日志输出

日志格式:
- 开发环境: 包含文件名和行号，便于调试
- 生产环境: 简洁格式，减少日志体积

配置来源:
- log_level: 从应用配置获取日志级别
- env: 从应用配置获取运行环境
"""

import logging
import logging.config
import sys
from typing import Any

from core.config import get_settings


def setup_logging() -> None:
    """初始化并配置应用日志系统

    流程:
    1. 获取应用配置中的日志级别
    2. 验证日志级别有效性，无效时默认使用 INFO
    3. 根据运行环境选择日志格式
    4. 构造并应用日志配置

    日志级别有效值:
    - DEBUG: 调试信息
    - INFO: 一般信息
    - WARNING: 警告信息
    - ERROR: 错误信息
    - CRITICAL: 严重错误

    Note:
        此函数应在应用启动时调用一次
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
        "disable_existing_loggers": False,  # 保留现有日志器
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
            # 根日志器配置
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
