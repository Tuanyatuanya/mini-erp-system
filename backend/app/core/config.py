from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./erp.db"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    APP_NAME: str = "Mini ERP"
    DEBUG: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
