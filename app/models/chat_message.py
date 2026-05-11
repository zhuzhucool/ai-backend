from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str
    user_id: int
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
