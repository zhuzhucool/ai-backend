from fastapi import APIRouter, Depends, HTTPException
from app.schemas.chat import ChatResponse, ChatRequest, Usage
from app.db.session import get_session
from app.models import chat_message
from sqlmodel import Session
import time
from app.core.security import verify_api_key, get_current_user_id
from app.models.llm_log import LLMLog
from app.services import llm
from app.core import config

settings = config.Settings()
router = APIRouter()


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
async def chat(req: ChatRequest, db: Session = Depends(get_session), user_id: str = Depends(get_current_user_id)):
    # TODO: 后面补事务、失败日志、Redis 限流/缓存、异步任务队列
    if not req.message.strip():
        raise HTTPException(status_code=400, detail={
            "error": "bad_request",
            "message": "message 不能为空"
        })
    
    user_message = ChatMessage(
        session_id=req.session_id,
        user_id=user_id,
        content=req.message,
        role="user"
    )

    db.add(user_message) #准备新增
    db.commit() #真正写入数据库
    db.refresh(user_message) #把数据库生成的ID信息读回来

    #日志记录
    start = time.perf_counter()
    success = False
    error_message = None
    response = None
    http_error = None
    llm_error = None
    try:
        response = await llm.llm_chat(req.message, req.temperature, req.max_tokens)
        success = True
    except llm.LLMError as e:
        error_message = e.message
        llm_error = e
        http_error = HTTPException(status_code=e.status_code, detail=e.message)
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)

    # 组装日志
    log = LLMLog(
        user_id=user_id,
        session_id=req.session_id,
        model=settings.OPENAI_MODEL,
        prompt_tokens=response.usage.prompt_tokens if response and response.usage else 0,
        completion_tokens=response.usage.completion_tokens if response and response.usage else 0,
        total_tokens=response.usage.total_tokens if response and response.usage else 0,
        latency_ms=latency_ms,
        success=success,
        error_message=error_message,
    )
    # 写入
    db.add(log)
    db.commit()

    if http_error:
        raise http_error from llm_error

    assistant_content = response.choices[0].message.content
    assistant_message = ChatMessage(
        session_id=req.session_id,
        user_id=user_id,
        content=assistant_content,
        role="assistant"
    )
    db.add(assistant_message) #准备新增
    db.commit() #真正写入数据库
    db.refresh(assistant_message) #把数据库生成的ID信息读回来

    result = ChatResponse(session_id=req.session_id,
                          message=response.choices[0].message.content,
                          model=settings.OPENAI_MODEL,
                          usage=Usage(
                                prompt_tokens = response.usage.prompt_tokens,
                                completion_tokens = response.usage.completion_tokens,
                                total_tokens = response.usage.total_tokens
                          )if response.usage else None
                        )
    return result
