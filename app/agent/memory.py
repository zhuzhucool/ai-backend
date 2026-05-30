from app.models.chat_message import ChatMessage
from sqlmodel import select
import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class ConversationMemoryError(Exception):
    pass

class ConversationMemory:
    """会话记忆管理"""
    
    def __init__(self, db_session, user_id: int):
        self.db = db_session
        self.user_id = user_id


    async def get_history(self, session_id: int, limit: int = 20) -> list:
        sql = (
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.user_id == self.user_id,
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )

        try:
            messages = self.db.exec(sql).all()
            messages.reverse()
        except SQLAlchemyError as exc:
            logger.exception("Failed to get conversation history")
            raise ConversationMemoryError("获取会话历史失败") from exc
        

        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]



    async def save(self, session_id: int, user_msg: str, assistant_msg: str):
        user_message = ChatMessage(
            session_id=session_id,
            user_id=self.user_id,
            role="user",
            content=user_msg,
        )

        assistant_message = ChatMessage(
            session_id=session_id,
            user_id=self.user_id,
            role="assistant",
            content=assistant_msg,
        )

        try:
            self.db.add(user_message)
            self.db.add(assistant_message)
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to save conversation memory")
            raise ConversationMemoryError("保存会话记忆失败") from exc


    
    async def update_summary(self, session_id: int):
        return None
