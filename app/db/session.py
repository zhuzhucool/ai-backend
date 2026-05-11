import os
from sqlmodel import Session, create_engine
from sqlalchemy import text
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

def check_database_connection() -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError(f"数据库连接失败: {exc}") from exc


def get_session():
    with Session(engine) as session:
        yield session