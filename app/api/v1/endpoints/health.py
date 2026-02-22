from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_health():
    return {"status": "ok", "message": "Service is healthy"}
