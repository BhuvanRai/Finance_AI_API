from fastapi import APIRouter
from app.api.v1.endpoints import health, rag, score, user_retrieval, analytics, simulate

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(score.router, prefix="/score", tags=["score"])
api_router.include_router(user_retrieval.router, prefix="/user-based-retrieval", tags=["user-based-retrieval"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(simulate.router, prefix="/simulate", tags=["simulate"])
