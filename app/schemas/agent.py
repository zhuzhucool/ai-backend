from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str
    session_id: int | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=1024 * 3)


class AgentToolCall(BaseModel):
    tool: str
    arguments: dict[str, Any]
    result: Any


class AgentChatResponse(BaseModel):
    session_id: int
    answer: str
    iterations: int
    tool_calls: list[AgentToolCall]


class AgentToolSchema(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class AgentToolsResponse(BaseModel):
    tools: list[AgentToolSchema]


class AgentToolLogItem(BaseModel):
    id: int
    session_id: int
    user_id: int
    tool: str
    arguments: Any
    result: Any
    iteration: int
    success: bool
    error_message: str | None = None
    created_at: datetime


class AgentToolLogListResponse(BaseModel):
    session_id: int
    tool_logs: list[AgentToolLogItem]
