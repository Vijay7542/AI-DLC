"""Base agent class for Mini AI-DLC."""

from typing import Optional, Any, Dict, List
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from config import Config, TestConfig


class BaseAgent:
    """Base class for all agents in Mini AI-DLC.

    Provides common utilities for LLM initialization, prompt management,
    and error handling. Designed to be modular and extensible.
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        use_test_config: bool = False,
    ):
        """Initialize the base agent.

        Args:
            llm: Optional LLM instance for testing with mocked responses
            use_test_config: If True, use TestConfig that doesn't require API key
        """
        self.config = TestConfig if use_test_config else Config
        self.llm = llm or self._initialize_llm()

    def _initialize_llm(self) -> BaseChatModel:
        """Initialize the LLM with Groq.

        Returns:
            Configured ChatGroq instance
        """
        try:
            self.config.validate()
            return ChatGroq(
                model=self.config.DEFAULT_MODEL,
                temperature=self.config.DEFAULT_TEMPERATURE,
                max_tokens=self.config.DEFAULT_MAX_TOKENS,
                api_key=self.config.GROQ_API_KEY,
            )
        except ValueError as e:
            if "GROQ_API_KEY" in str(e):
                # For testing, return a mock LLM if no API key
                return self._create_mock_llm()
            raise

    def _create_mock_llm(self) -> BaseChatModel:
        """Create a mock LLM for testing without API key.

        Note: This is a placeholder. In actual tests, use unittest.mock
        to properly mock the LLM for complete control over responses.
        """
        raise ValueError(
            "Mock LLM not implemented. Use unittest.mock in tests "
            "to mock the LLM with controlled responses."
        )

    def invoke_llm(
        self,
        messages: List[BaseMessage],
        **kwargs: Any,
    ) -> BaseMessage:
        """Invoke the LLM with messages.

        Args:
            messages: List of messages to send to LLM
            **kwargs: Additional arguments for LLM invocation

        Returns:
            LLM response message
        """
        try:
            response = self.llm.invoke(messages, **kwargs)
            return response
        except Exception as e:
            raise RuntimeError(f"LLM invocation failed: {e}") from e

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
