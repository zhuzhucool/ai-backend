from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str 
    session_id: int = 123
    temperature: float = Field(ge=0.0, le=2.0)
    max_tokens: int = Field(ge=1, le=1024*3)

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatResponse(BaseModel):
    session_id: int
    message: str
    model: str
    usage: Usage | None