import logging
import sys
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1.api import api_router
from app.api.v2.api import api_v2_router
from app.api.v3.api import api_v3_router
from app.core.config import settings
from app.core.logging import setup_logging

def get_application() -> FastAPI:
    # Setup structured logging
    setup_logging()
    
    _app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # Set all CORS enabled origins
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @_app.get("/", tags=["root"])
    async def root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "docs": "/docs",
            "health": f"{settings.API_V1_STR}/health"
        }

    _app.include_router(api_router, prefix=settings.API_V1_STR)
    _app.include_router(api_v2_router, prefix="/api/v2")
    _app.include_router(api_v3_router, prefix="/api/v3")

    return _app

app = get_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
