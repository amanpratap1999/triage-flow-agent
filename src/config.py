import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PORT: int = int(os.getenv("PORT", "8002"))
    HOST: str = os.getenv("HOST", "127.0.0.1")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tickets.db")

    # Policy threshold
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))

    # LLM Configuration
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "").strip()
    MOCK_LLM: bool = os.getenv("MOCK_LLM", "true").lower() in ("true", "1", "yes") or not LLM_API_KEY
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").lower()
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

settings = Settings()
