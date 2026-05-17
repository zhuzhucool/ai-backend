from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    ENV: str
    OPENAI_BASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    DATABASE_URL: str
    API_KEY: str
    EMBEDDING_URL: str
    EMBEDDING_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-v4"
    EMBEDDING_DIM: int = 1024

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()