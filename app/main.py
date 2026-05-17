from fastapi import FastAPI
from app.core import config
from contextlib import asynccontextmanager
from app.db.session import check_database_connection
from app.db.init_db import init_db
from fastapi import FastAPI
from app.api import health
from app.api import chat
from app.api import documents
from app.api import knowledge
from app.api import messages

@asynccontextmanager
async def lifespan(app: FastAPI):
    check_database_connection()
    init_db()
    yield
settings = config.Settings()
print(settings)


app = FastAPI(lifespan=lifespan)
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(knowledge.router)
app.include_router(messages.router)









    


# unset OPENAI_API_KEY OPENAI_MODEL OPENAI_BASE_URL DATABASE_URL API_KEY APP_NAME ENV

#uvicorn app.main:app --reload --port 18001