from pathlib import Path
from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).parent / ".env"


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    taapi_secret: str

    model_config = {"env_file": str(_ENV_FILE)}


settings = Settings()
