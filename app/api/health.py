from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def chat_health():
    return {"status": "ok", "service": "ai-backend"}
