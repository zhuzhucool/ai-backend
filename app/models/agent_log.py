from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AgentToolLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int
    user_id: int
    tool: str
    arguments: str
    result: str
    iteration: int
    success: bool = True
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
