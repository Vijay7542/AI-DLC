"""Configuration management for Mini AI-DLC."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    # LLM Provider Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    LLM_FALLBACK_PROVIDERS: str = os.getenv("LLM_FALLBACK_PROVIDERS", "")

    # Groq API Configuration (legacy support)
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")

    # OpenAI API Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # Anthropic API Configuration
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # Default model configuration
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 4096

    # LLM invocation configuration
    DEFAULT_TIMEOUT: int = 30  # seconds per LLM call
    MAX_RETRIES: int = 3  # number of retries for transient errors
    RETRY_DELAY: float = 1.0  # initial delay in seconds (exponential backoff)

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        # Check if at least one API key is available
        has_credentials = any([
            cls.GROQ_API_KEY,
            cls.OPENAI_API_KEY,
            cls.ANTHROPIC_API_KEY,
        ])
        
        if not has_credentials:
            raise ValueError(
                "No LLM API key found. Please set GROQ_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in your environment or .env file."
            )


# For testing: allow config to work without API key
class TestConfig(Config):
    """Test configuration that doesn't require API key."""

    # Override timeouts for faster testing
    DEFAULT_TIMEOUT: int = 5  # shorter timeout for tests
    MAX_RETRIES: int = 1  # fewer retries for tests
    RETRY_DELAY: float = 0.1  # shorter delay for tests

    @classmethod
    def validate(cls) -> None:
        """Skip validation for testing."""
        pass
