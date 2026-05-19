from pydantic import BaseModel
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    status: str
    chunks_count: int

class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    created_at: datetime

class DocumentListResponse(BaseModel):
    total: int
    documents: list[DocumentResponse]

class DocumentDeleteResponse(BaseModel):
    document_id: int
    status: str