from fastapi import FastAPI

from core.config import get_settings

settings = get_settings()
print(settings.model_dump())

app = FastAPI()
