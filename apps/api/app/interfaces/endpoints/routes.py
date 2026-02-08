from fastapi import APIRouter

from . import status_routes


def create_api_routes() -> APIRouter:
    api_router = APIRouter()
    api_router.include_router(status_routes.router)
    return api_router


router = create_api_routes()
