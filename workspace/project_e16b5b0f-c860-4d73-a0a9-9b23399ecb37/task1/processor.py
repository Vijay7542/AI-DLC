"""Task 1 processing module.

This module provides the core implementation for Task 1. It is deliberately
kept simple to serve as a concrete example of a production‑ready Python
component.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List

logger = logging.getLogger(__name__)


@dataclass
class Task1Result:
    """Container for the result of a Task 1 run.

    Attributes
    ----------
    success: bool
        Indicates whether the task completed successfully.
    data: Any
        Arbitrary data produced by the task. The concrete type depends on the
        specific use‑case.
    messages: List[str]
        Human‑readable messages generated during processing.
    """

    success: bool
    data: Any = None
    messages: List[str] | None = None

    def __post_init__(self) -> None:
        if self.messages is None:
            self.messages = []


class Task1Processor:
    """Processor class encapsulating the logic for Task 1.

    The class is designed to be easily extensible and testable. All heavy
    lifting should be performed by injected callables so that the behaviour can
    be mocked in unit tests.
    """

    def __init__(
        self,
        data_source: Callable[[], Iterable[Any]] | None = None,
        transformer: Callable[[Any], Any] | None = None,
    ) -> None:
        """Create a new :class:`Task1Processor`.

        Parameters
        ----------
        data_source:
            A callable returning an iterable of raw items to process. If ``None``
            a default in‑memory source is used.
        transformer:
            A callable that transforms a single raw item into the desired output
            format. If ``None`` the identity function is used.
        """
        self._data_source = data_source or self._default_data_source
        self._transformer = transformer or (lambda x: x)
        logger.debug("Task1Processor initialized with data_source=%s, transformer=%s",
                     self._data_source, self._transformer)

    @staticmethod
    def _default_data_source() -> Iterable[Any]:
        """Yield a small default dataset.

        This method exists so that the processor can run without external
        dependencies. In a real‑world scenario the data source would likely be a
        database query, an HTTP request, or a file read.
        """
        logger.debug("Using default data source")
        return [1, 2, 3, 4, 5]

    def run(self) -> Task1Result:
        """Execute the task and return a :class:`Task1Result`.

        The method iterates over the data source, applies the transformer to each
        element, collects the results, and records any errors that occur.
        """
        logger.info("Task 1 execution started")
        processed_items: List[Any] = []
        messages: List[str] = []
        success = True

        try:
            for raw_item in self._data_source():
                logger.debug("Processing raw_item=%s", raw_item)
                try:
                    transformed = self._transformer(raw_item)
                    processed_items.append(transformed)
                    logger.debug("Transformed item=%s", transformed)
                except Exception as exc:  # pylint: disable=broad-except
                    success = False
                    error_msg = f"Error processing item {raw_item!r}: {exc}"
                    messages.append(error_msg)
                    logger.exception(error_msg)
        except Exception as exc:  # pylint: disable=broad-except
            # Unexpected failure while obtaining the data source itself.
            success = False
            error_msg = f"Data source failure: {exc}"
            messages.append(error_msg)
            logger.exception(error_msg)

        result = Task1Result(success=success, data=processed_items, messages=messages)
        logger.info("Task 1 execution finished with success=%s", success)
        return result

    def __call__(self) -> Task1Result:
        """Allow the processor instance to be called directly.

        ``processor()`` is equivalent to ``processor.run()`` and provides a concise
        syntax for interactive use.
        """
        return self.run()
