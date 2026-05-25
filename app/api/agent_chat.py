import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.agent.loop import AgentLoop
from app.agent.memory import ConversationMemory, ConversationMemoryError
from app.agent.tool_log import AgentToolLogWriter, AgentToolLogWriterError
from app.agent.tools.calculator import CalculatorTool
from app.agent.tools.get_time import GetCurrentTimeTool
from app.agent.tools.knowledge_search import KnowledgeSearchTool
from app.agent.tools.registry import ToolRegistry
from app.core import config
from app.core.security import get_current_user_id, verify_api_key
from app.db.session import get_session
from app.models.agent_log import AgentToolLog
from app.models.llm_log import LLMLog
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentToolCall,
    AgentToolLogItem,
    AgentToolLogListResponse,
    AgentToolsResponse,
    AgentToolSchema,
)
from app.services.llm import LLMError, LLMService
from app.services.rag_service import RagService


settings = config.Settings()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])


def build_tool_registry(user_id: int) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(GetCurrentTimeTool())
    registry.register(KnowledgeSearchTool(RagService(user_id=user_id)))
    return registry


def parse_json_value(value: str):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Agent 聊天对话",
)
async def chat(
    req: AgentChatRequest,
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail={
            "error": "bad_request",
            "message": "message 不能为空",
        })

    session_id = req.session_id
    if session_id is None:
        session_id = int(time.time() * 1000)
    logger.info("agent chat start user_id=%s session_id=%s message_len=%s", user_id, session_id, len(req.message))
    llm_service = LLMService(settings.OPENAI_API_KEY, settings.OPENAI_BASE_URL, settings.OPENAI_MODEL)
    registry = build_tool_registry(user_id)
    memory = ConversationMemory(db, user_id)
    tool_log_writer = AgentToolLogWriter(db, user_id)
    agent = AgentLoop(llm_service, registry, memory=memory, tool_log_writer=tool_log_writer)

    start = time.perf_counter()
    success = False
    error_message = None
    result = None

    try:
        result = await agent.run(req.message, session_id)
        success = True
        logger.info("agent chat success user_id=%s session_id=%s iterations=%s tool_calls=%s", user_id, session_id, result["iterations"], len(result["tool_calls"]))
    except LLMError as exc:
        db.rollback()
        error_message = exc.message
        logger.exception("agent chat llm failed user_id=%s session_id=%s", user_id, session_id)
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except (ConversationMemoryError, AgentToolLogWriterError) as exc:
        db.rollback()
        error_message = str(exc)
        logger.exception("agent chat persistence failed user_id=%s session_id=%s", user_id, session_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        error_message = str(exc)
        logger.exception("agent chat unexpected failed user_id=%s session_id=%s", user_id, session_id)
        raise HTTPException(status_code=500, detail="Agent 服务异常") from exc
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        try:
            db.add(LLMLog(
                user_id=user_id,
                session_id=session_id,
                model=settings.OPENAI_MODEL,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message,
            ))
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("agent chat llm log save failed user_id=%s session_id=%s", user_id, session_id)

    return AgentChatResponse(
        session_id=session_id,
        answer=result["answer"],
        iterations=result["iterations"],
        tool_calls=[
            AgentToolCall(
                tool=tool_call["tool"],
                arguments=tool_call["arguments"],
                result=parse_json_value(tool_call["result"]),
            )
            for tool_call in result["tool_calls"]
        ],
    )


@router.get(
    "/tools",
    response_model=AgentToolsResponse,
    dependencies=[Depends(verify_api_key)],
    summary="查询 Agent 可用工具",
)
async def list_tools(user_id: int = Depends(get_current_user_id)):
    registry = build_tool_registry(user_id)
    tools = [
        AgentToolSchema(
            name=schema["function"]["name"],
            description=schema["function"]["description"],
            parameters=schema["function"]["parameters"],
        )
        for schema in registry.get_schemas()
    ]
    return AgentToolsResponse(tools=tools)


@router.get(
    "/sessions/{session_id}/tool-logs",
    response_model=AgentToolLogListResponse,
    dependencies=[Depends(verify_api_key)],
    summary="查询 Agent 工具调用日志",
)
async def get_tool_logs(
    session_id: int,
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    sql = (
        select(AgentToolLog)
        .where(
            AgentToolLog.session_id == session_id,
            AgentToolLog.user_id == user_id,
        )
        .order_by(AgentToolLog.created_at)
    )
    logs = db.exec(sql).all()

    return AgentToolLogListResponse(
        session_id=session_id,
        tool_logs=[
            AgentToolLogItem(
                id=log.id,
                session_id=log.session_id,
                user_id=log.user_id,
                tool=log.tool,
                arguments=parse_json_value(log.arguments),
                result=parse_json_value(log.result),
                iteration=log.iteration,
                success=log.success,
                error_message=log.error_message,
                created_at=log.created_at,
            )
            for log in logs
        ],
    )
