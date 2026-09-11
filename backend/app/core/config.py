import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "Intelligent Document Extraction, Validation & API Platform"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./doc_intelligence.db")
    
    # File validation constraints
    MAX_PAGE_LIMIT: int = 3
    ALLOWED_MIME_TYPES: List[str] = ["application/pdf", "image/jpeg", "image/png"]
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".jpg", ".jpeg", ".png"]
    MAX_FILE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    
    # Validation engine parameters
    NUMERICAL_TOLERANCE: float = 0.05
    
    # Optional LLM API keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./storage/uploads")

settings = Settings()
