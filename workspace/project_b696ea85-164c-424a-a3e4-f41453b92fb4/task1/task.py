"""Task 1 implementation module.

This module provides a simple `Task1` class that encapsulates the
business logic for the first task in the project. The implementation is
kept deliberately straightforward to serve as a solid foundation for
future extensions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Optional


@dataclass
class TaskResult:
    """Container for the result of a task execution.

    Attributes
    ----------
    success: bool
        Indicates whether the task completed successfully.
    data: Any, optional
        The payload produced by the task, if any.
    errors: List[str]
        A list of error messages collected during execution.
    """

    success: bool
    data: Optional[Any] = None
    errors: List[str] = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []

    def add_error(self, message: str) -> None:
        """Append an error message to the result.

        Parameters
        ----------
        message: str
            The error description to record.
        """
        self.errors.append(message)
        self.success = False

    def __repr__(self) -> str:
        return (
            f"TaskResult(success={self.success}, "
            f"data={self.data!r}, errors={self.errors})"
        )


class Task1:
    """Concrete implementation of the first task.

    The class is designed to be easily testable and extensible. It accepts a
    callable `processor` that performs the core work; this allows dependency
    injection for unit testing or alternative processing strategies.
    """

    def __init__(self, processor: Callable[[Any], Any] | None = None) -> None:
        """Create a new ``Task1`` instance.

        Parameters
        ----------
        processor: Callable[[Any], Any] | None, optional
            A function that receives an input payload and returns a processed
            result. If omitted, a default identity processor is used.
        """
        self.processor = processor or (lambda x: x)

    def run(self, payload: Any = None) -> TaskResult:
        """Execute the task with the provided ``payload``.

        The method captures any exception raised by the processor and returns
        a :class:`TaskResult` describing the outcome.

        Parameters
        ----------
        payload: Any, optional
            Input data for the processor. If ``None`` the processor receives
            ``None``.

        Returns
        -------
        TaskResult
            The result object containing success status, processed data, and
            any errors.
        """
        result = TaskResult(success=True)
        try:
            processed = self.processor(payload)
            result.data = processed
        except Exception as exc:  # pragma: no cover – defensive programming
            result.add_error(str(exc))
        return result

    def __repr__(self) -> str:
        return f"Task1(processor={self.processor})"
