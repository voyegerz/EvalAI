from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils, upload, download, evaluate, collections, evaluations
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(upload.router)
api_router.include_router(download.router)
api_router.include_router(evaluate.router)
api_router.include_router(collections.router)
api_router.include_router(evaluations.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
