"""Multi-provider LLM abstraction layer.

Supports Groq, OpenAI, and Anthropic with configurable fallback.
"""

import os
import logging
from typing import Optional, List, Any, Dict
from enum import Enum
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMErrorType(Enum):
    """Types of LLM errors for classification."""
    RATE_LIMIT = "rate_limit"
    QUOTA_EXHAUSTED = "quota_exhausted"
    AUTHENTICATION_FAILED = "authentication_failed"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    INVALID_MODEL = "invalid_model"
    INVALID_RESPONSE = "invalid_response"
    UNKNOWN = "unknown"


class LLMProviderConfig:
    """Configuration for an LLM provider."""
    
    def __init__(
        self,
        provider: LLMProvider,
        model: str,
        api_key_env_var: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.provider = provider
        self.model = model
        self.api_key_env_var = api_key_env_var
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment."""
        return os.getenv(self.api_key_env_var)
    
    def has_credentials(self) -> bool:
        """Check if credentials are available."""
        return bool(self.get_api_key())


class LLMProviderManager:
    """Manages multiple LLM providers with fallback support."""
    
    def __init__(self, provider_configs: List[LLMProviderConfig]):
        """Initialize the provider manager.
        
        Args:
            provider_configs: List of provider configurations in fallback order
        """
        self.provider_configs = provider_configs
        self.current_provider_index = 0
        self._llm_cache: Dict[int, BaseChatModel] = {}
    
    def get_llm(self) -> BaseChatModel:
        """Get the current LLM instance.
        
        Returns:
            Configured LLM instance
        """
        config = self.provider_configs[self.current_provider_index]
        
        if self.current_provider_index not in self._llm_cache:
            self._llm_cache[self.current_provider_index] = self._create_llm(config)
        
        return self._llm_cache[self.current_provider_index]
    
    def _create_llm(self, config: LLMProviderConfig) -> BaseChatModel:
        """Create an LLM instance for the given configuration.
        
        Args:
            config: Provider configuration
            
        Returns:
            Configured LLM instance
        """
        api_key = config.get_api_key()
        
        if config.provider == LLMProvider.GROQ:
            logger.info(f"Creating Groq LLM with model: {config.model}")
            return ChatGroq(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=api_key,
            )
        elif config.provider == LLMProvider.OPENAI:
            logger.info(f"Creating OpenAI LLM with model: {config.model}")
            return ChatOpenAI(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=api_key,
            )
        elif config.provider == LLMProvider.ANTHROPIC:
            logger.info(f"Creating Anthropic LLM with model: {config.model}")
            return ChatAnthropic(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=api_key,
            )
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    def get_current_provider(self) -> LLMProvider:
        """Get the current provider being used.
        
        Returns:
            Current LLM provider
        """
        return self.provider_configs[self.current_provider_index].provider
    
    def try_next_provider(self) -> bool:
        """Attempt to switch to the next available provider.
        
        Returns:
            True if switched successfully, False if no more providers available
        """
        for i in range(self.current_provider_index + 1, len(self.provider_configs)):
            if self.provider_configs[i].has_credentials():
                self.current_provider_index = i
                logger.info(f"Switched to provider: {self.provider_configs[i].provider.value}")
                return True
        
        logger.warning("No more providers available with credentials")
        return False
    
    def classify_error(self, error: Exception) -> LLMErrorType:
        """Classify an LLM error.
        
        Args:
            error: Exception from LLM invocation
            
        Returns:
            Error type classification
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Rate limit (HTTP 429)
        if "429" in error_str or "rate limit" in error_str:
            # Check if it's a permanent quota exhaustion
            if "quota" in error_str or ("limit" in error_str and ("tokens per day" in error_str or "requests per day" in error_str)):
                return LLMErrorType.QUOTA_EXHAUSTED
            return LLMErrorType.RATE_LIMIT
        
        # Authentication
        if "authentication" in error_str or "auth" in error_str or "unauthorized" in error_str or "invalid api key" in error_str:
            return LLMErrorType.AUTHENTICATION_FAILED
        
        # Network
        if "connection" in error_str or "network" in error_str:
            return LLMErrorType.NETWORK_ERROR
        
        # Timeout
        if "timeout" in error_str:
            return LLMErrorType.TIMEOUT
        
        # Invalid model
        if "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
            return LLMErrorType.INVALID_MODEL
        
        # Default
        return LLMErrorType.UNKNOWN
    
    def should_retry(self, error_type: LLMErrorType) -> bool:
        """Determine if an error should trigger a retry.
        
        Args:
            error_type: Type of error
            
        Returns:
            True if retry should be attempted
        """
        # Retry rate limits, network errors, timeouts
        if error_type in [LLMErrorType.RATE_LIMIT, LLMErrorType.NETWORK_ERROR, LLMErrorType.TIMEOUT]:
            return True
        
        # Don't retry quota exhaustion, auth failures, invalid model
        return False
    
    def should_fallback(self, error_type: LLMErrorType) -> bool:
        """Determine if an error should trigger provider fallback.
        
        Args:
            error_type: Type of error
            
        Returns:
            True if fallback to next provider should be attempted
        """
        # Fallback on quota exhaustion, auth failures, invalid model
        if error_type in [LLMErrorType.QUOTA_EXHAUSTED, LLMErrorType.AUTHENTICATION_FAILED, LLMErrorType.INVALID_MODEL]:
            return True
        
        return False


def create_provider_manager_from_env() -> LLMProviderManager:
    """Create provider manager from environment variables.
    
    Environment variables:
    - LLM_PROVIDER: Primary provider (groq, openai, anthropic)
    - LLM_MODEL: Model name
    - LLM_FALLBACK_PROVIDERS: Comma-separated list of fallback providers
    
    Returns:
        Configured provider manager
    """
    primary_provider_str = os.getenv("LLM_PROVIDER", "groq").lower()
    primary_model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    
    # Map provider string to enum
    provider_map = {
        "groq": LLMProvider.GROQ,
        "openai": LLMProvider.OPENAI,
        "anthropic": LLMProvider.ANTHROPIC,
    }
    
    primary_provider = provider_map.get(primary_provider_str, LLMProvider.GROQ)
    
    # API key environment variables
    api_key_map = {
        LLMProvider.GROQ: "GROQ_API_KEY",
        LLMProvider.OPENAI: "OPENAI_API_KEY",
        LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
    }
    
    # Default models for each provider
    default_models = {
        LLMProvider.GROQ: "openai/gpt-oss-120b",
        LLMProvider.OPENAI: "gpt-4o",
        LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    }
    
    # Build provider configurations
    configs = []
    
    # Primary provider
    configs.append(LLMProviderConfig(
        provider=primary_provider,
        model=primary_model,
        api_key_env_var=api_key_map[primary_provider],
    ))
    
    # Fallback providers
    fallback_str = os.getenv("LLM_FALLBACK_PROVIDERS", "")
    if fallback_str:
        for fallback in fallback_str.split(","):
            fallback = fallback.strip().lower()
            if fallback in provider_map and fallback != primary_provider_str:
                configs.append(LLMProviderConfig(
                    provider=provider_map[fallback],
                    model=default_models[provider_map[fallback]],
                    api_key_env_var=api_key_map[provider_map[fallback]],
                ))
    
    logger.info(f"Provider manager configured with {len(configs)} provider(s)")
    for i, config in enumerate(configs):
        logger.info(f"  {i+1}. {config.provider.value} ({config.model}) - credentials: {config.has_credentials()}")
    
    return LLMProviderManager(configs)
