from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    bot_token: str
    database_url: str
    redis_url: str
    r2_endpoint: str
    r2_bucket: str
    r2_key: str
    r2_secret: str
    allowed_origins: str = "https://seedhunter.vercel.app"
    auth_max_age: int = 3600

    class Config:
        env_file = ".env"

@lru_cache
def settings() -> Settings:
    return Settings()