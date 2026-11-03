"""Tests for multi-provider LLM architecture."""

import pytest
import os
from unittest.mock import Mock, patch
from agents.llm_provider import (
    LLMProvider,
    LLMProviderConfig,
    LLMProviderManager,
    LLMErrorType,
    create_provider_manager_from_env,
)
from langchain_core.messages import AIMessage


def test_llm_provider_config_creation():
    """Test LLMProviderConfig creation."""
    config = LLMProviderConfig(
        provider=LLMProvider.GROQ,
        model="openai/gpt-oss-120b",
        api_key_env_var="GROQ_API_KEY",
    )
    
    assert config.provider == LLMProvider.GROQ
    assert config.model == "openai/gpt-oss-120b"
    assert config.api_key_env_var == "GROQ_API_KEY"


def test_llm_provider_config_has_credentials():
    """Test credential availability check."""
    # Set a test API key
    os.environ["TEST_API_KEY"] = "test_key_123"
    
    config = LLMProviderConfig(
        provider=LLMProvider.GROQ,
        model="test-model",
        api_key_env_var="TEST_API_KEY",
    )
    
    assert config.has_credentials() is True
    assert config.get_api_key() == "test_key_123"
    
    # Cleanup
    del os.environ["TEST_API_KEY"]


def test_llm_provider_config_no_credentials():
    """Test credential check when key is missing."""
    config = LLMProviderConfig(
        provider=LLMProvider.GROQ,
        model="test-model",
        api_key_env_var="NONEXISTENT_API_KEY",
    )
    
    assert config.has_credentials() is False
    assert config.get_api_key() is None


def test_provider_manager_initialization():
    """Test LLMProviderManager initialization."""
    configs = [
        LLMProviderConfig(
            provider=LLMProvider.GROQ,
            model="model1",
            api_key_env_var="GROQ_API_KEY",
        ),
        LLMProviderConfig(
            provider=LLMProvider.OPENAI,
            model="model2",
            api_key_env_var="OPENAI_API_KEY",
        ),
    ]
    
    manager = LLMProviderManager(configs)
    
    assert len(manager.provider_configs) == 2
    assert manager.current_provider_index == 0
    assert manager.get_current_provider() == LLMProvider.GROQ


def test_provider_manager_switching():
    """Test provider switching."""
    os.environ["TEST_KEY_1"] = "key1"
    os.environ["TEST_KEY_2"] = "key2"
    
    configs = [
        LLMProviderConfig(
            provider=LLMProvider.GROQ,
            model="model1",
            api_key_env_var="TEST_KEY_1",
        ),
        LLMProviderConfig(
            provider=LLMProvider.OPENAI,
            model="model2",
            api_key_env_var="TEST_KEY_2",
        ),
    ]
    
    manager = LLMProviderManager(configs)
    
    assert manager.get_current_provider() == LLMProvider.GROQ
    
    # Switch to next provider
    success = manager.try_next_provider()
    
    assert success is True
    assert manager.get_current_provider() == LLMProvider.OPENAI
    
    # Try to switch again (no more providers)
    success = manager.try_next_provider()
    assert success is False
    
    # Cleanup
    del os.environ["TEST_KEY_1"]
    del os.environ["TEST_KEY_2"]


def test_error_classification_rate_limit():
    """Test rate limit error classification."""
    error = Exception("Error code: 429 - Rate limit exceeded")
    manager = LLMProviderManager([])
    
    error_type = manager.classify_error(error)
    
    assert error_type == LLMErrorType.RATE_LIMIT


def test_error_classification_quota_exhausted():
    """Test quota exhaustion error classification."""
    error = Exception("Rate limit reached - tokens per day (TPD): Limit 200000, Used 200000")
    manager = LLMProviderManager([])
    
    error_type = manager.classify_error(error)
    
    assert error_type == LLMErrorType.QUOTA_EXHAUSTED


def test_error_classification_authentication():
    """Test authentication error classification."""
    error = Exception("AuthenticationError: Invalid API key")
    manager = LLMProviderManager([])
    
    error_type = manager.classify_error(error)
    
    assert error_type == LLMErrorType.AUTHENTICATION_FAILED


def test_error_classification_network():
    """Test network error classification."""
    error = Exception("ConnectionError: Network unreachable")
    manager = LLMProviderManager([])
    
    error_type = manager.classify_error(error)
    
    assert error_type == LLMErrorType.NETWORK_ERROR


def test_error_classification_timeout():
    """Test timeout error classification."""
    error = Exception("TimeoutError: Request timed out")
    manager = LLMProviderManager([])
    
    error_type = manager.classify_error(error)
    
    assert error_type == LLMErrorType.TIMEOUT


def test_should_retry_rate_limit():
    """Test that rate limits should be retried."""
    manager = LLMProviderManager([])
    
    assert manager.should_retry(LLMErrorType.RATE_LIMIT) is True
    assert manager.should_retry(LLMErrorType.NETWORK_ERROR) is True
    assert manager.should_retry(LLMErrorType.TIMEOUT) is True


def test_should_not_retry_quota_exhausted():
    """Test that quota exhaustion should not be retried."""
    manager = LLMProviderManager([])
    
    assert manager.should_retry(LLMErrorType.QUOTA_EXHAUSTED) is False
    assert manager.should_retry(LLMErrorType.AUTHENTICATION_FAILED) is False
    assert manager.should_retry(LLMErrorType.INVALID_MODEL) is False


def test_should_fallback_quota_exhausted():
    """Test that quota exhaustion should trigger fallback."""
    manager = LLMProviderManager([])
    
    assert manager.should_fallback(LLMErrorType.QUOTA_EXHAUSTED) is True
    assert manager.should_fallback(LLMErrorType.AUTHENTICATION_FAILED) is True
    assert manager.should_fallback(LLMErrorType.INVALID_MODEL) is True


def test_should_not_fallback_rate_limit():
    """Test that rate limits should not trigger fallback (should retry instead)."""
    manager = LLMProviderManager([])
    
    assert manager.should_fallback(LLMErrorType.RATE_LIMIT) is False
    assert manager.should_fallback(LLMErrorType.NETWORK_ERROR) is False


def test_create_provider_manager_from_env():
    """Test creating provider manager from environment variables."""
    os.environ["LLM_PROVIDER"] = "groq"
    os.environ["LLM_MODEL"] = "llama-3.3-70b-versatile"
    os.environ["GROQ_API_KEY"] = "test_key"
    
    manager = create_provider_manager_from_env()
    
    assert len(manager.provider_configs) == 1
    assert manager.provider_configs[0].provider == LLMProvider.GROQ
    assert manager.provider_configs[0].model == "llama-3.3-70b-versatile"
    
    # Cleanup
    del os.environ["LLM_PROVIDER"]
    del os.environ["LLM_MODEL"]
    del os.environ["GROQ_API_KEY"]


def test_create_provider_manager_with_fallback():
    """Test creating provider manager with fallback providers."""
    os.environ["LLM_PROVIDER"] = "groq"
    os.environ["LLM_FALLBACK_PROVIDERS"] = "openai,anthropic"
    os.environ["GROQ_API_KEY"] = "key1"
    os.environ["OPENAI_API_KEY"] = "key2"
    os.environ["ANTHROPIC_API_KEY"] = "key3"
    
    manager = create_provider_manager_from_env()
    
    assert len(manager.provider_configs) == 3
    assert manager.provider_configs[0].provider == LLMProvider.GROQ
    assert manager.provider_configs[1].provider == LLMProvider.OPENAI
    assert manager.provider_configs[2].provider == LLMProvider.ANTHROPIC
    
    # Cleanup
    del os.environ["LLM_PROVIDER"]
    del os.environ["LLM_FALLBACK_PROVIDERS"]
    del os.environ["GROQ_API_KEY"]
    del os.environ["OPENAI_API_KEY"]
    del os.environ["ANTHROPIC_API_KEY"]


def test_provider_manager_no_credentials_all():
    """Test provider manager when no provider has credentials."""
    configs = [
        LLMProviderConfig(
            provider=LLMProvider.GROQ,
            model="model1",
            api_key_env_var="NONEXISTENT_KEY_1",
        ),
        LLMProviderConfig(
            provider=LLMProvider.OPENAI,
            model="model2",
            api_key_env_var="NONEXISTENT_KEY_2",
        ),
    ]
    
    manager = LLMProviderManager(configs)
    
    # Should not be able to switch (no credentials)
    success = manager.try_next_provider()
    assert success is False


def test_provider_manager_skip_without_credentials():
    """Test that try_next_provider skips providers without credentials."""
    os.environ["TEST_KEY_1"] = "key1"
    
    configs = [
        LLMProviderConfig(
            provider=LLMProvider.GROQ,
            model="model1",
            api_key_env_var="NONEXISTENT_KEY",
        ),
        LLMProviderConfig(
            provider=LLMProvider.OPENAI,
            model="model2",
            api_key_env_var="TEST_KEY_1",
        ),
    ]
    
    manager = LLMProviderManager(configs)
    
    # Should skip first provider (no credentials) and switch to second
    success = manager.try_next_provider()
    assert success is True
    assert manager.get_current_provider() == LLMProvider.OPENAI
    
    # Cleanup
    del os.environ["TEST_KEY_1"]
