"""Task 1 implementation module.

This module provides a simple example implementation for "Task 1". The
function `execute_task1` takes a list of integers and returns their sum. The
behaviour is deliberately straightforward to serve as a placeholder for a
real-world task implementation.

The design follows Python best practices:
- Type hints are used for all public signatures.
- A clear docstring explains the purpose, arguments, and return value.
- The function is pure (no side‑effects) which makes it easy to test.
"""

from __future__ import annotations

from typing import List


def execute_task1(data: List[int]) -> int:
    """Execute Task 1.

    Args:
        data: A list of integers to be processed.

    Returns:
        The sum of the integers in ``data``.

    Example:
        >>> execute_task1([1, 2, 3])
        6
    """
    return sum(data)
