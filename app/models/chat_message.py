from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, Integer
from sqlmodel import SQLModel, Field


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, sa_column=Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True))
    session_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    user_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
