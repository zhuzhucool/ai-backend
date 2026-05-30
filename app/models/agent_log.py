from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, Integer
from sqlmodel import Field, SQLModel


class AgentToolLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, sa_column=Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True))
    session_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    user_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    tool: str
    arguments: str
    result: str
    iteration: int
    success: bool = True
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
