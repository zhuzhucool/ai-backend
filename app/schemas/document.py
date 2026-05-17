from pydantic import BaseModel
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    status: str

class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    created_at: datetime