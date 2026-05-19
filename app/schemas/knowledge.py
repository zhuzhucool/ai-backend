from pydantic import BaseModel

class SourceResponse(BaseModel):
    file: str
    page: int | None = None
    similarity: float

class KnowledgeQueryResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    confidence: str

class KnowledgeSearchResult(BaseModel):
    text: str
    source_file: str
    page_number: int | None = None
    section_title: str | None = None
    similarity: float
    low_confidence: bool

class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeSearchResult]
