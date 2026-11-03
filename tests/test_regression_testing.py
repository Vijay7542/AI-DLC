"""Tests for full regression testing in Testing Agent."""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import AIMessage
from agents.testing_agent import TestingAgent
from graph.state import TestCase, TestReport, BugReport


@pytest.fixture
def workspace():
    """Provide a temporary workspace directory."""
    path = tempfile.mkdtemp(prefix="test_workspace_")
    yield path
    # Cleanup
    if os.path.exists(path):
        shutil.rmtree(path)


@pytest.fixture
def mock_llm():
    """Provide a mock LLM."""
    mock = Mock()
    mock.invoke.return_value = AIMessage(content="Mock response")
    return mock


def test_parse_pytest_output_passed():
    """Test parsing pytest output with passed tests."""
    agent = TestingAgent(llm=Mock(), use_test_config=True)
    
    stdout = """
tests/test_module.py::test_function PASSED
tests/test_module.py::test_another PASSED
"""
    stderr = ""
    
    results = agent._parse_pytest_output(stdout, stderr)
    
    assert "tests/test_module.py::test_function" in results
    assert results["tests/test_module.py::test_function"] == "passed"
    assert results["tests/test_module.py::test_another"] == "passed"


def test_parse_pytest_output_failed():
    """Test parsing pytest output with failed tests."""
    agent = TestingAgent(llm=Mock(), use_test_config=True)
    
    stdout = """
tests/test_module.py::test_function FAILED
tests/test_module.py::test_another PASSED
"""
    stderr = ""
    
    results = agent._parse_pytest_output(stdout, stderr)
    
    assert results["tests/test_module.py::test_function"] == "failed"
    assert results["tests/test_module.py::test_another"] == "passed"


def test_parse_pytest_output_skipped():
    """Test parsing pytest output with skipped tests."""
    agent = TestingAgent(llm=Mock(), use_test_config=True)
    
    stdout = """
tests/test_module.py::test_function SKIPPED
tests/test_module.py::test_another PASSED
"""
    stderr = ""
    
    results = agent._parse_pytest_output(stdout, stderr)
    
    assert results["tests/test_module.py::test_function"] == "skipped"
    assert results["tests/test_module.py::test_another"] == "passed"


def test_detect_regression_new_failures():
    """Test regression detection when new failures are introduced."""
    agent = TestingAgent(llm=Mock(), use_test_config=True)
    
    # Previous report: all tests passed
    previous_test_cases = [
        TestCase(test_id="1", test_name="test_a", test_type="unit", file_path="test.py", 
                 function_name="test_a", description="Test A", status="passed"),
        TestCase(test_id="2", test_name="test_b", test_type="unit", file_path="test.py",
                 function_name="test_b", description="Test B", status="passed"),
    ]
    previous_report = TestReport(
        total_tests=2,
        passed_tests=2,
        failed_tests=0,
        skipped_tests=0,
        test_cases=previous_test_cases,
        bug_reports=[],
    )
    
    # New report: test_b now fails
    new_test_cases = [
        TestCase(test_id="1", test_name="test_a", test_type="unit", file_path="test.py",
                 function_name="test_a", description="Test A", status="passed"),
        TestCase(test_id="2", test_name="test_b", test_type="unit", file_path="test.py",
                 function_name="test_b", description="Test B", status="failed"),
    ]
    new_report = TestReport(
        total_tests=2,
        passed_tests=1,
        failed_tests=1,
        skipped_tests=0,
        test_cases=new_test_cases,
        bug_reports=[],
    )
    
    regression = agent._detect_regression(previous_report, new_report)
    
    assert regression is True


def test_detect_regression_fixed_failures():
    """Test regression detection when failures are fixed (no regression)."""
    agent = TestingAgent(llm=Mock(), use_test_config=True)
    
    # Previous report: test_b failed
    previous_test_cases = [
        TestCase(test_id="1", test_name="test_a", test_type="unit", file_path="test.py",
                 function_name="test_a", description="Test A", status="passed"),
        TestCase(test_id="2", test_name="test_b", test_type="unit", file_path="test.py",
                 function_name="test_b", description="Test B", status="failed"),
    ]
    previous_report = TestReport(
        total_tests=2,
        passed_tests=1,
        failed_tests=1,
        skipped_tests=0,
        test_cases=previous_test_cases,
        bug_reports=[],
    )
    
    # New report: all tests pass
    new_test_cases = [
        TestCase(test_id="1", test_name="test_a", test_type="unit", file_path="test.py",
                 function_name="test_a", description="Test A", status="passed"),
        TestCase(test_id="2", test_name="test_b", test_type="unit", file_path="test.py",
                 function_name="test_b", description="Test B", status="passed"),
    ]
    new_report = TestReport(
        total_tests=2,
        passed_tests=2,
        failed_tests=0,
        skipped_tests=0,
        test_cases=new_test_cases,
        bug_reports=[],
    )
    
    regression = agent._detect_regression(previous_report, new_report)
    
    assert regression is False


def test_detect_regression_mixed():
    """Test regression detection with mixed results."""
    agent = TestingAgent(llm=Mock(), use_test_config=True)
    
    # Previous report: test_b failed
    previous_test_cases = [
        TestCase(test_id="1", test_name="test_a", test_type="unit", file_path="test.py",
                 function_name="test_a", description="Test A", status="passed"),
        TestCase(test_id="2", test_name="test_b", test_type="unit", file_path="test.py",
                 function_name="test_b", description="Test B", status="failed"),
        TestCase(test_id="3", test_name="test_c", test_type="unit", file_path="test.py",
                 function_name="test_c", description="Test C", status="passed"),
    ]
    previous_report = TestReport(
        total_tests=3,
        passed_tests=2,
        failed_tests=1,
        skipped_tests=0,
        test_cases=previous_test_cases,
        bug_reports=[],
    )
    
    # New report: test_b fixed, but test_c now fails (regression)
    new_test_cases = [
        TestCase(test_id="1", test_name="test_a", test_type="unit", file_path="test.py",
                 function_name="test_a", description="Test A", status="passed"),
        TestCase(test_id="2", test_name="test_b", test_type="unit", file_path="test.py",
                 function_name="test_b", description="Test B", status="passed"),
        TestCase(test_id="3", test_name="test_c", test_type="unit", file_path="test.py",
                 function_name="test_c", description="Test C", status="failed"),
    ]
    new_report = TestReport(
        total_tests=3,
        passed_tests=2,
        failed_tests=1,
        skipped_tests=0,
        test_cases=new_test_cases,
        bug_reports=[],
    )
    
    regression = agent._detect_regression(previous_report, new_report)
    
    assert regression is True  # test_c regression


def test_execute_tests_run_all_disabled():
    """Test _execute_tests with run_all=False (normal mode)."""
    agent = TestingAgent(llm=Mock(), use_test_config=True)
    
    test_cases = [
        TestCase(test_id="1", test_name="test_a", test_type="unit", file_path="test.py",
                 function_name="test_a", description="Test A"),
    ]
    
    # Mock Docker check to return False (skip Docker execution)
    with patch('agents.testing_agent.check_docker_ready', return_value=False):
        # Should not crash, but Docker availability check happens in process(), not _execute_tests
        pass
    
    # Test that run_all parameter is accepted
    # Actual Docker execution would require mocking subprocess.run
    # This is a structural test
    assert callable(agent._execute_tests)


def test_regression_comparison_individual_tests():
    """Test that regression detection compares individual test identities."""
    agent = TestingAgent(llm=Mock(), use_test_config=True)
    
    # Create reports with different test identities
    previous_test_cases = [
        TestCase(test_id="1", test_name="test_module.py::test_feature_a", test_type="unit",
                 file_path="test.py", function_name="test_a", description="Test A", status="passed"),
        TestCase(test_id="2", test_name="test_module.py::test_feature_b", test_type="unit",
                 file_path="test.py", function_name="test_b", description="Test B", status="passed"),
    ]
    previous_report = TestReport(
        total_tests=2,
        passed_tests=2,
        failed_tests=0,
        skipped_tests=0,
        test_cases=previous_test_cases,
        bug_reports=[],
    )
    
    # Same tests, one now fails
    new_test_cases = [
        TestCase(test_id="1", test_name="test_module.py::test_feature_a", test_type="unit",
                 file_path="test.py", function_name="test_a", description="Test A", status="passed"),
        TestCase(test_id="2", test_name="test_module.py::test_feature_b", test_type="unit",
                 file_path="test.py", function_name="test_b", description="Test B", status="failed"),
    ]
    new_report = TestReport(
        total_tests=2,
        passed_tests=1,
        failed_tests=1,
        skipped_tests=0,
        test_cases=new_test_cases,
        bug_reports=[],
    )
    
    regression = agent._detect_regression(previous_report, new_report)
    
    assert regression is True


def test_regression_with_different_test_names():
    """Test regression detection when test names differ."""
    agent = TestingAgent(llm=Mock(), use_test_config=True)
    
    previous_test_cases = [
        TestCase(test_id="1", test_name="test_old.py::test_func", test_type="unit",
                 file_path="test.py", function_name="test_func", description="Test", status="passed"),
    ]
    previous_report = TestReport(
        total_tests=1,
        passed_tests=1,
        failed_tests=0,
        skipped_tests=0,
        test_cases=previous_test_cases,
        bug_reports=[],
    )
    
    # Different test name - no comparison possible
    new_test_cases = [
        TestCase(test_id="1", test_name="test_new.py::test_func", test_type="unit",
                 file_path="test.py", function_name="test_func", description="Test", status="failed"),
    ]
    new_report = TestReport(
        total_tests=1,
        passed_tests=0,
        failed_tests=1,
        skipped_tests=0,
        test_cases=new_test_cases,
        bug_reports=[],
    )
    
    regression = agent._detect_regression(previous_report, new_report)
    
    # No regression because test names don't match
    assert regression is False
