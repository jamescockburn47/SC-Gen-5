"""
Pydantic settings for LexCognito RAG v2.
"""

from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Model directory - where quantized models are stored
    MODEL_DIR: Path = Path("models")
    
    # Database and storage paths
    DATA_DIR: Path = Path("data")
    VECTOR_STORE_DIR: Path = Path("vectorstores")
    
    # Model configurations - LAZY LOADING
    MAIN_MODEL: str = "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"  # Main Mistral-7B model
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"  # Match existing vector database
    
    # Lazy loading settings
    LAZY_LOADING: bool = True  # Models load on first use
    ENABLE_GPU_ACCELERATION: bool = True  # Auto-detect GPU usage
    
    # Utility model settings (DISABLED)
    ENABLE_UTILITY_MODEL: bool = False  # Completely disabled
    UTILITY_MODEL: str = "TinyLlama-1.1B"  # Not used when disabled
    UTILITY_MODEL_THRESHOLD: float = 0.5  # Not used when disabled
    
    # Hardware settings
    MAX_GPU_MEMORY_FRACTION: float = 0.85  # Reduced for stability
    CPU_THREADS: int = 8
    FAISS_THREADS: int = 8
    
    # API settings
    API_HOST: str = "127.0.0.1"  # Changed to localhost for security
    API_PORT: int = 8001  # Changed to avoid conflicts
    API_WORKERS: int = 1  # Single worker for stability
    DEBUG: bool = False
    
    # WebSocket settings
    WS_MAX_CONNECTIONS: int = 100
    WS_TIMEOUT: int = 300  # 5 minutes
    
    # RAG settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVAL_K: int = 10
    MAX_CONTEXT_LENGTH: int = 8192  # Increased for Mistral-7B
    
    # Security
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables

# Global settings instance
settings = Settings()