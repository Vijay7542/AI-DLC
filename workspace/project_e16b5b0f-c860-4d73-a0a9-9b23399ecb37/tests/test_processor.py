"""Unit tests for :mod:`task1.processor`.

The tests focus on the public API of :class:`Task1Processor`. They verify that
custom data sources and transformers are honoured and that error handling works
as expected.
"""

from __future__ import annotations

import pytest

from task1.processor import Task1Processor, Task1Result


def test_default_run_success() -> None:
    processor = Task1Processor()
    result: Task1Result = processor.run()
    assert result.success
    assert result.data == [1, 2, 3, 4, 5]
    assert result.messages == []


def test_custom_data_source() -> None:
    def source():
        return ["a", "b", "c"]

    processor = Task1Processor(data_source=source)
    result = processor.run()
    assert result.success
    assert result.data == ["a", "b", "c"]


def test_transformer_applied() -> None:
    def source():
        return [1, 2, 3]

    def double(x: int) -> int:
        return x * 2

    processor = Task1Processor(data_source=source, transformer=double)
    result = processor.run()
    assert result.success
    assert result.data == [2, 4, 6]


def test_error_handling_in_transformer() -> None:
    def source():
        return [1, 0, 2]

    def safe_divide(x: int) -> float:
        return 10 / x  # will raise ZeroDivisionError for x == 0

    processor = Task1Processor(data_source=source, transformer=safe_divide)
    result = processor.run()
    # The zero division should be caught, overall success becomes False
    assert not result.success
    # Two successful transformations, one failed (the zero)
    assert result.data == [10.0, 5.0]
    assert any("ZeroDivisionError" in msg for msg in result.messages)


def test_callable_interface() -> None:
    processor = Task1Processor()
    result = processor()  # __call__ should delegate to run()
    assert isinstance(result, Task1Result)
    assert result.success
