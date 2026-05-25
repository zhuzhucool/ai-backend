from sqlmodel import SQLModel

from app.db.session import engine
from app.models.document import Document
from app.models.chat_message import ChatMessage
from app.models.llm_log import LLMLog
from app.models.document_embedding import DocumentEmbedding
from app.models.retrieval_log import RetrievalLog
from app.models.agent_log import AgentToolLog

def init_db() -> None:
    SQLModel.metadata.create_all(engine)
