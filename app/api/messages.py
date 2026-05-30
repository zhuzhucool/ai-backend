from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.chat_message import ChatMessage
from app.db.session import get_session
from sqlmodel import Session, select
from app.core.security import verify_api_key, get_current_user_id
from datetime import datetime

router = APIRouter(tags=["Messages"])


def make_session_title(messages: list[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user" and message.content.strip():
            return message.content.strip()[:24]
    for message in reversed(messages):
        if message.content.strip():
            return message.content.strip()[:24]
    return "未命名对话"


def make_session_summary(messages: list[ChatMessage]) -> str:
    latest = messages[0]
    created_at = latest.created_at
    if isinstance(created_at, datetime):
        time_text = created_at.strftime("%m-%d %H:%M")
    else:
        time_text = str(created_at)
    count = len(messages)
    return f"{count} 条消息 · 最近 {time_text}"


@router.get(
    "/sessions",
    dependencies=[Depends(verify_api_key)],
    summary="查询当前用户会话列表",
    description="返回当前用户最近有消息的会话，用于前端历史对话列表。",
)
async def list_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    sql = (
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit * 50)
    )
    rows = db.exec(sql).all()

    grouped: dict[int, list[ChatMessage]] = {}
    for row in rows:
        grouped.setdefault(row.session_id, []).append(row)
        if len(grouped) >= limit and all(grouped.values()):
            continue

    sessions = []
    for session_id, session_messages in list(grouped.items())[:limit]:
        latest = session_messages[0]
        sessions.append({
            "id": str(session_id),
            "session_id": session_id,
            "title": make_session_title(session_messages),
            "summary": make_session_summary(session_messages),
            "message_count": len(session_messages),
            "updated_at": latest.created_at,
        })

    return {"sessions": sessions}


@router.get(
    "/sessions/{session_id}/messages",
    dependencies=[Depends(verify_api_key)],
    summary="查询会话消息",
    description="按会话 ID 查询当前用户的聊天历史，返回按创建时间排序的消息列表。",
)
async def get_message(session_id: int, db: Session = Depends(get_session), user_id: int = Depends(get_current_user_id)):
    if session_id == None:
        raise HTTPException(status_code=400, detail={
            "error": "bad_request",
            "session_id": "session_id 不能为空"
            })
    sql = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id, ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at)
    )
    messages = db.exec(sql).all()
    return {"session_id": session_id, "messages" : messages}
