from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseModel):
    """Application configuration settings"""
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/gym_db"
    )
    database_host: str = os.getenv("DATABASE_HOST", "localhost")
    database_port: int = int(os.getenv("DATABASE_PORT", 5432))
    database_name: str = os.getenv("DATABASE_NAME", "gym_db")
    database_user: str = os.getenv("DATABASE_USER", "postgres")
    database_password: str = os.getenv("DATABASE_PASSWORD", "password")
    
    # FastAPI
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    api_title: str = os.getenv("API_TITLE", "Gym Management System API")
    api_version: str = os.getenv("API_VERSION", "1.0.0")
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
