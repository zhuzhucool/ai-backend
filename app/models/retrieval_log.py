from datetime import datetime
from sqlalchemy import BigInteger, Column, Integer
from sqlmodel import SQLModel, Field

class RetrievalLog(SQLModel, table=True):
    __tablename__ = "retrieval_logs"

    id: int | None = Field(default=None, sa_column=Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True))
    user_id: int = Field(sa_column=Column(BigInteger, nullable=False, index=True))
    query: str
    top_k: int
    results_count: int
    top_similarity: float | None = None
    latency_ms: int = Field(sa_column=Column(BigInteger, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
