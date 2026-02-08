from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    app_name: str = "Multi-User Todo Web Application"
    version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    
    # Database settings
    database_url: str
    
    # JWT settings
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Better Auth settings
    better_auth_secret: str
    
    # Groq settings
    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"
    
    # Allowed origins for CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]
    
    class Config:
        env_file = ".env"


settings = Settings()