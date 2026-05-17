from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field

class DocumentEmbedding(SQLModel, table=True):
    __tablename__ = "document_embeddings"
    id: int = Field(default=None, primary_key=True)
    doc_id: int = Field(index=True)
    owner_id: int = Field(index=True)
    chunk_text: str
    chunk_index: int
    source_file: str
    page_number: int | None = None
    section_title: str | None = None
    embedding: list[float] = Field(sa_column=Column(Vector(1024)))
    metadata_: dict | None = Field(default=None, sa_column=Column(JSON))