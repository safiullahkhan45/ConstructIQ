"""
Application configuration settings
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    app_name: str = "Austin Permits Semantic Search API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "text-embedding-3-small"
    
    # PostgreSQL Database
    database_url: str = ""
    database_echo: bool = False
    
    # Logging
    log_level: str = "info"
    log_file: str = "query_logs.log"
    
    # Data Processing
    date_formats: List[str] = [
        "%Y-%m-%d", 
        "%m/%d/%Y", 
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f"
    ]
    currency_symbols: List[str] = ["$", "USD", "usd"]
    zip_pattern: str = r"\d{5}(-\d{4})?"
    
    # Search
    default_search_limit: int = 5
    max_search_limit: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()