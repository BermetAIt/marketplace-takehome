from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Marketplace API"
    DEBUG: bool = False
    API_PUBLIC_BASE_URL: str = "http://127.0.0.1:8000"

    # Database
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "marketplace"

    # JWT
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60

    # Uploads (local dev; swap for object storage URLs in production)
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LISTING_MAX_IMAGES: int = 12
    MESSAGE_MAX_ATTACHMENTS: int = 5

    @property
    def DATABASE_URL(self) -> str:
        pwd = self.MYSQL_PASSWORD
        if pwd:
            from urllib.parse import quote_plus

            pwd = quote_plus(pwd)
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{pwd}@"
            f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def upload_path(self) -> Path:
        return Path(self.UPLOAD_DIR).resolve()

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()