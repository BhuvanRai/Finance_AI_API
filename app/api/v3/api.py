from fastapi import APIRouter
from app.api.v1.endpoints import analytics, simulate

api_v3_router = APIRouter()
api_v3_router.include_router(analytics.router, prefix="/analytics", tags=["v3 - analytics"])
api_v3_router.include_router(simulate.router, prefix="/simulate", tags=["v3 - simulate"])
