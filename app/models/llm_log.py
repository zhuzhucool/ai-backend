from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, Integer
from sqlmodel import SQLModel, Field


class LLMLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, sa_column=Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True))
    user_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    session_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, nullable=True))
    model: str
    prompt_tokens: int = Field(default=0, sa_column=Column(BigInteger, nullable=False, default=0))
    completion_tokens: int = Field(default=0, sa_column=Column(BigInteger, nullable=False, default=0))
    total_tokens: int = Field(default=0, sa_column=Column(BigInteger, nullable=False, default=0))
    latency_ms: Optional[int] = Field(default=None, sa_column=Column(BigInteger, nullable=True))
    success: bool = False
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
