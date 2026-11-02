"""Configuration management for Mini AI-DLC."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    # Groq API Configuration
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")

    # Default model configuration
    DEFAULT_MODEL: str = "llama-3.3-70b-versatile"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 4096

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not set. Please set it in your environment or .env file."
            )


# For testing: allow config to work without API key
class TestConfig(Config):
    """Test configuration that doesn't require API key."""

    @classmethod
    def validate(cls) -> None:
        """Skip validation for testing."""
        pass
