"""Tests for BaseAgent with mocked LLM."""

import pytest
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
    mock_llm.invoke.assert_called_once_with(messages)


def test_base_agent_invoke_llm_error_handling():
    """Test error handling when LLM invocation fails."""
    mock_llm = Mock()
    mock_llm.invoke.side_effect = Exception("LLM error")

    agent = BaseAgent(llm=mock_llm)
    messages = [SystemMessage(content="Test")]

    with pytest.raises(RuntimeError, match="LLM invocation failed"):
        agent.invoke_llm(messages)


def test_base_agent_with_test_config():
    """Test BaseAgent with TestConfig (no API key required)."""
    mock_llm = Mock()
    agent = BaseAgent(llm=mock_llm, use_test_config=True)
    assert agent.config == TestConfig


def test_base_agent_without_llm_raises_error():
    """Test that BaseAgent requires an LLM instance or valid config."""
    with pytest.raises(ValueError, match="Mock LLM not implemented"):
        BaseAgent(llm=None, use_test_config=False)
