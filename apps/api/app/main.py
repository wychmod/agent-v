import logging

from fastapi import FastAPI

from app.infrastructure.logging import setup_logging
from core.config import get_settings

settings = get_settings()

setup_logging()
logger = logging.getLogger()

logger.info("测试")
app = FastAPI()
