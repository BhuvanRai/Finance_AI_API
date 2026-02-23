from fastapi import APIRouter
from app.api.v1.endpoints import user_retrieval

api_v2_router = APIRouter()
api_v2_router.include_router(user_retrieval.router, prefix="/user-based-retrieval", tags=["v2 - user-based-retrieval"])
