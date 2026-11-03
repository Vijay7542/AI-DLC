"""Base agent class for Mini AI-DLC."""

import time
import logging
import random
from typing import Optional, Any, Dict, List
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from config import Config, TestConfig
from agents.llm_provider import LLMProviderManager, create_provider_manager_from_env, LLMErrorType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all agents in Mini AI-DLC.

    Provides common utilities for LLM initialization, prompt management,
    and error handling. Designed to be modular and extensible.
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        use_test_config: bool = False,
        provider_manager: Optional[LLMProviderManager] = None,
    ):
        """Initialize the base agent.

        Args:
            llm: Optional LLM instance for testing with mocked responses
            use_test_config: If True, use TestConfig that doesn't require API key
            provider_manager: Optional provider manager for multi-provider support
        """
        self.config = TestConfig if use_test_config else Config
        self.llm = llm or self._initialize_llm(provider_manager)

    def _initialize_llm(self, provider_manager: Optional[LLMProviderManager] = None) -> BaseChatModel:
        """Initialize the LLM with multi-provider support.

        Args:
            provider_manager: Optional provider manager instance

        Returns:
            Configured LLM instance
        """
        try:
            if use_test_config := isinstance(self.config, TestConfig):
                logger.info("Using test configuration")
                return self._create_mock_llm()
            
            # Use provided provider manager or create from environment
            if provider_manager is None:
                logger.info("Creating provider manager from environment")
                provider_manager = create_provider_manager_from_env()
            
            self.provider_manager = provider_manager
            llm = provider_manager.get_llm()
            logger.info(f"LLM initialized with provider: {provider_manager.get_current_provider().value}")
            return llm
            
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            # For testing, return a mock LLM if no API key
            return self._create_mock_llm()

    def _create_mock_llm(self) -> BaseChatModel:
        """Create a mock LLM for testing without API key.

        Returns a simple mock that returns predefined responses.
        For proper testing, use unittest.mock in tests for complete control.
        """
        class MockLLM:
            def invoke(self, messages, **kwargs):
                return AIMessage(content="Mock response - LLM not configured")

        return MockLLM()

    def invoke_llm(
        self,
        messages: List[BaseMessage],
        **kwargs: Any,
    ) -> BaseMessage:
        """Invoke the LLM with messages, with retry and provider fallback.

        Args:
            messages: List of messages to send to LLM
            **kwargs: Additional arguments for LLM invocation

        Returns:
            LLM response message

        Raises:
            RuntimeError: If LLM invocation fails after all retries and fallbacks
        """
        timeout = kwargs.pop('timeout', self.config.DEFAULT_TIMEOUT)
        
        # Check if we have a provider manager (for multi-provider support)
        provider_manager = getattr(self, 'provider_manager', None)
        
        if provider_manager:
            return self._invoke_with_fallback(messages, provider_manager, timeout, **kwargs)
        else:
            return self._invoke_simple(messages, timeout, **kwargs)
    
    def _invoke_simple(
        self,
        messages: List[BaseMessage],
        timeout: int,
        **kwargs: Any,
    ) -> BaseMessage:
        """Simple LLM invocation without fallback (legacy support).
        
        Args:
            messages: List of messages to send to LLM
            timeout: Request timeout
            **kwargs: Additional arguments
            
        Returns:
            LLM response message
        """
        max_retries = self.config.MAX_RETRIES
        retry_delay = self.config.RETRY_DELAY

        logger.info(f"Invoking LLM with {len(messages)} messages, timeout={timeout}s, max_retries={max_retries}")

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"LLM invocation attempt {attempt + 1}/{max_retries + 1}")
                response = self.llm.invoke(messages, timeout=timeout, **kwargs)
                logger.info(f"LLM response received, content length: {len(response.content) if hasattr(response, 'content') else 'N/A'}")
                return response
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                logger.error(f"LLM invocation failed on attempt {attempt + 1}: {error_type}: {str(e)}")

                # Don't retry on certain errors
                if error_type in ['ValueError', 'AuthenticationError', 'PermissionError']:
                    raise RuntimeError(f"LLM invocation failed: {e}") from e

                # If not the last attempt, wait and retry
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)

        # All retries exhausted
        raise RuntimeError(f"LLM invocation failed after {max_retries} retries: {last_error}") from last_error
    
    def _invoke_with_fallback(
        self,
        messages: List[BaseMessage],
        provider_manager: LLMProviderManager,
        timeout: int,
        **kwargs: Any,
    ) -> BaseMessage:
        """Invoke LLM with provider fallback support.
        
        Args:
            messages: List of messages to send to LLM
            provider_manager: Provider manager instance
            timeout: Request timeout
            **kwargs: Additional arguments
            
        Returns:
            LLM response message
        """
        max_providers = len(provider_manager.provider_configs)
        current_provider_index = provider_manager.current_provider_index
        
        for provider_attempt in range(max_providers):
            current_provider = provider_manager.get_current_provider()
            logger.info(f"Attempting provider: {current_provider.value} (attempt {provider_attempt + 1}/{max_providers})")
            
            try:
                llm = provider_manager.get_llm()
                response = self._invoke_with_retry(llm, messages, provider_manager, timeout, **kwargs)
                logger.info(f"Successfully invoked LLM using provider: {current_provider.value}")
                return response
                
            except Exception as e:
                error_type = provider_manager.classify_error(e)
                logger.error(f"Provider {current_provider.value} failed: {error_type.value} - {str(e)}")
                
                # Check if we should try next provider
                if provider_manager.should_fallback(error_type):
                    if provider_manager.try_next_provider():
                        continue
                    else:
                        # No more providers available
                        break
                else:
                    # Don't fallback, just raise
                    raise RuntimeError(f"LLM invocation failed: {e}") from e
        
        # All providers exhausted
        raise RuntimeError(f"LLM invocation failed on all {max_providers} providers") from e
    
    def _invoke_with_retry(
        self,
        llm: BaseChatModel,
        messages: List[BaseMessage],
        provider_manager: LLMProviderManager,
        timeout: int,
        **kwargs: Any,
    ) -> BaseMessage:
        """Invoke LLM with retry logic.
        
        Args:
            llm: LLM instance
            messages: List of messages
            provider_manager: Provider manager for error classification
            timeout: Request timeout
            **kwargs: Additional arguments
            
        Returns:
            LLM response message
        """
        max_retries = self.config.MAX_RETRIES
        retry_delay = self.config.RETRY_DELAY

        logger.info(f"Invoking LLM with {len(messages)} messages, timeout={timeout}s, max_retries={max_retries}")

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"LLM invocation attempt {attempt + 1}/{max_retries + 1}")
                response = llm.invoke(messages, timeout=timeout, **kwargs)
                
                # Validate response
                if not hasattr(response, 'content') or not response.content:
                    raise ValueError("Invalid LLM response: missing content")
                
                logger.info(f"LLM response received, content length: {len(response.content)}")
                return response
                
            except Exception as e:
                last_error = e
                error_type = provider_manager.classify_error(e)
                logger.error(f"LLM invocation failed on attempt {attempt + 1}: {error_type.value}: {str(e)}")

                # Check if we should retry
                if not provider_manager.should_retry(error_type):
                    raise RuntimeError(f"LLM invocation failed: {e}") from e

                # If not the last attempt, wait and retry with jitter
                if attempt < max_retries:
                    jitter = random.uniform(0.5, 1.5)
                    wait_time = retry_delay * (2 ** attempt) * jitter  # Exponential backoff with jitter
                    logger.info(f"Retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)

        # All retries exhausted
        raise RuntimeError(f"LLM invocation failed after {max_retries} retries: {last_error}") from last_error

    def create_system_prompt(self, content: str) -> SystemMessage:
        """Create a system message.

        Args:
            content: System prompt content

        Returns:
            SystemMessage instance
        """
        return SystemMessage(content=content)

    def create_user_prompt(self, content: str) -> HumanMessage:
        """Create a user message.

        Args:
            content: User prompt content

        Returns:
            HumanMessage instance
        """
        return HumanMessage(content=content)
