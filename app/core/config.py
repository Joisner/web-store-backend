from pydantic_settings import BaseSettings
from typing import List, Union
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI E-commerce Backend"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/fastapi_db")

    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_changed_in_production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS settings
    # BACKEND_CORS_ORIGINS can be a string of comma-separated origins, or a list of strings.
    # Defaulting to allow Angular dev server and a common localhost variant.
    _raw_cors_origins: str = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200,http://localhost:8080")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self._raw_cors_origins.split(',') if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        # Extra = 'ignore' # If you want to allow extra fields in .env not defined in Settings
        extra = "allow"

settings = Settings()

# To test CORS settings:
# print("Allowed CORS Origins:", settings.BACKEND_CORS_ORIGINS)
# print("Allowed CORS Origins:", settings.BACKEND_CORS_ORIGINS)
