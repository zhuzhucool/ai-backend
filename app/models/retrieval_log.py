from datetime import datetime
from sqlmodel import SQLModel, Field

class RetrievalLog(SQLModel, table=True):
    __tablename__ = "retrieval_logs"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    query: str
    top_k: int
    results_count: int
    top_similarity: float | None = None
    latency_ms: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
