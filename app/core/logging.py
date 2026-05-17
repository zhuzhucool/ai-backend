import logging
from fastapi import APIRouter, Request
import time

router = APIRouter()

logger = logging.getLogger("app.request")
logging.basicConfig(level=logging.INFO)
@router.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "request failed method=%s path=%s duration_ms=%.2f error=%s",
            request.method,
            request.url.path,
            duration_ms,
            str(exc),
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "request completed method=%s path=%s status_code=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response