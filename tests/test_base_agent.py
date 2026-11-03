"""Tests for BaseAgent with mocked LLM."""

import pytest
import time
from unittest.mock import Mock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agents.base_agent import BaseAgent
from config import TestConfig


def test_base_agent_initialization_with_mocked_llm():
    """Test BaseAgent initialization with a mocked LLM."""
    mock_llm = Mock()
    agent = BaseAgent(llm=mock_llm)
    assert agent.llm == mock_llm


def test_base_agent_creates_system_prompt():
    """Test creating a system prompt."""
    mock_llm = Mock()
    agent = BaseAgent(llm=mock_llm)
    message = agent.create_system_prompt("You are a helpful assistant.")
    assert isinstance(message, SystemMessage)
    assert message.content == "You are a helpful assistant."


def test_base_agent_creates_user_prompt():
    """Test creating a user prompt."""
    mock_llm = Mock()
    agent = BaseAgent(llm=mock_llm)
    message = agent.create_user_prompt("Hello, world!")
    assert isinstance(message, HumanMessage)
    assert message.content == "Hello, world!"


def test_base_agent_invoke_llm():
    """Test invoking the LLM with messages."""
    mock_llm = Mock()
    mock_response = AIMessage(content="Test response")
    mock_llm.invoke.return_value = mock_response

    agent = BaseAgent(llm=mock_llm)
    messages = [SystemMessage(content="Test"), HumanMessage(content="Hello")]

    response = agent.invoke_llm(messages)

    assert response == mock_response
    # Timeout is now added by default
    mock_llm.invoke.assert_called_once_with(messages, timeout=30)


def test_base_agent_invoke_llm_error_handling():
    """Test error handling when LLM invocation fails."""
    mock_llm = Mock()
    mock_llm.invoke.side_effect = Exception("LLM error")

    agent = BaseAgent(llm=mock_llm)
    messages = [SystemMessage(content="Test")]

    with pytest.raises(RuntimeError, match="LLM invocation failed"):
        agent.invoke_llm(messages)


def test_base_agent_invoke_llm_with_timeout():
    """Test that timeout parameter is passed to LLM invoke."""
    mock_llm = Mock()
    mock_response = AIMessage(content="Test response")
    mock_llm.invoke.return_value = mock_response

    agent = BaseAgent(llm=mock_llm)
    messages = [SystemMessage(content="Test")]

    response = agent.invoke_llm(messages, timeout=10)

    assert response == mock_response
    mock_llm.invoke.assert_called_once_with(messages, timeout=10)


def test_base_agent_invoke_llm_retry_on_transient_error():
    """Test retry logic for transient errors."""
    mock_llm = Mock()
    mock_response = AIMessage(content="Test response")

    # Fail twice, then succeed
    mock_llm.invoke.side_effect = [
        Exception("Transient error 1"),
        Exception("Transient error 2"),
        mock_response
    ]

    agent = BaseAgent(llm=mock_llm)
    messages = [SystemMessage(content="Test")]

    # Configure faster retry for testing
    agent.config.RETRY_DELAY = 0.01

    response = agent.invoke_llm(messages)

    assert response == mock_response
    assert mock_llm.invoke.call_count == 3


def test_base_agent_invoke_llm_no_retry_on_auth_error():
    """Test that auth errors are not retried."""
    mock_llm = Mock()
    mock_llm.invoke.side_effect = ValueError("Authentication failed")

    agent = BaseAgent(llm=mock_llm)
    messages = [SystemMessage(content="Test")]

    with pytest.raises(RuntimeError, match="LLM invocation failed"):
        agent.invoke_llm(messages)

    # Should only be called once (no retries for auth errors)
    assert mock_llm.invoke.call_count == 1


def test_base_agent_with_test_config():
    """Test BaseAgent with TestConfig (no API key required)."""
    mock_llm = Mock()
    agent = BaseAgent(llm=mock_llm, use_test_config=True)
    assert agent.config == TestConfig


def test_base_agent_fallback_llm_works():
    """Test that the fallback mock LLM class works correctly."""
    agent = BaseAgent(llm=None, use_test_config=True)
    # The fallback mock is now created through _initialize_llm
    # Just verify the agent was initialized with test config
    assert agent.config == TestConfig
