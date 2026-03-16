"""
Configuration settings for the Job Recommendation System.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "AI Job Recommendation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    PORT: int = 8000
    
    # MongoDB Configuration
    MONGODB_URL: str = "mongodb+srv://aditya17103:LTYQ5GBMhuV3V4Kn@template.foxz9eg.mongodb.net/"
    DATABASE_NAME: str = "job_recommendation_db"
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = ""
    SECRET_KEY: str = ""
    
    # AI/ML Model Configuration
    # Model should be loaded from .env
    EMBEDDING_MODEL: str 
    EMBEDDING_DIMENSION: int
    
    # Recommendation Weights (must sum to 1.0)
    SEMANTIC_WEIGHT: float = 0.40
    SKILL_MATCH_WEIGHT: float = 0.35
    PREFERENCE_WEIGHT: float = 0.25
    
    # Recommendation Settings
    TOP_K_RECOMMENDATIONS: int = 10
    SIMILARITY_THRESHOLD: float = 0.3
    
    # CORS
    CORS_ORIGINS: list = ["*", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]
    
    class Config:
        env_file = ".env" 
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
