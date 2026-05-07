from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    ENV: str
    OPENAI_BASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    DATABASE_URL: str
    API_KEY: str

    model_config = SettingsConfigDict(env_file=".env")