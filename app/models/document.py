from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, Integer
from sqlmodel import SQLModel, Field


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, sa_column=Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True))
    user_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    filename: str
    file_path: str
    content_type: Optional[str] = None
    size: Optional[int] = Field(default=None, sa_column=Column(BigInteger, nullable=True))
    status: str = "pending"
    text_content: Optional[str] = None  # 没提取到内容就存 None
    created_at: datetime = Field(default_factory=datetime.utcnow)
