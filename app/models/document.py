from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    filename: str
    file_path: str
    content_type: Optional[str] = None
    size: Optional[int] = None
    status: str = "pending"
    text_content: Optional[str] = None  # 没提取到内容就存 None
    created_at: datetime = Field(default_factory=datetime.utcnow)
