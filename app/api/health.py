from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="健康检查",
    description="用于确认服务进程是否正常运行，不依赖业务鉴权。",
)
async def chat_health():
    return {"status": "ok", "service": "ai-backend"}
