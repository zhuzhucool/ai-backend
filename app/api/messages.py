from fastapi import APIRouter, Depends, HTTPException
from app.models.chat_message import ChatMessage
from app.db.session import get_session
from sqlmodel import Session, select
from app.core.security import verify_api_key, get_current_user_id
from app.core import config

settings = config.Settings()
router = APIRouter()


@router.get("/sessions/{session_id}/messages", dependencies=[Depends(verify_api_key)])
async def get_message(session_id: int, db: Session = Depends(get_session), user_id: str = Depends(get_current_user_id)):
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