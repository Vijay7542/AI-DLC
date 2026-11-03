import logging
from dataclasses import dataclass
from typing import Any, Dict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@dataclass
class Task1Result:
    """Result container for Task 1 execution.

    Attributes
    ----------
    success: bool
        Indicates whether the task completed successfully.
    data: Dict[str, Any]
        Arbitrary data produced by the task.
    message: str
        Human‑readable description of the outcome.
    """

    success: bool
    data: Dict[str, Any]
    message: str

class Task1Runner:
    """Core implementation for Task 1.

    The runner encapsulates the business logic for the task. It can be
    instantiated with configuration parameters if needed (currently none).
    """

    def __init__(self) -> None:
        logger.debug("Task1Runner initialized")

    def run(self) -> Task1Result:
        """Execute Task 1.

        Returns
        -------
        Task1Result
            A result object describing the execution outcome.
        """
        logger.info("Starting Task 1 execution")
        try:
            # Placeholder for real business logic.
            # For demonstration, we simply return a success message.
            result_data = {"detail": "Task 1 performed successfully"}
            logger.debug("Task 1 result data: %s", result_data)
            return Task1Result(
                success=True,
                data=result_data,
                message="Task 1 completed successfully"
            )
        except Exception as exc:  # pragma: no cover – defensive programming
            logger.exception("Task 1 failed with an exception")
            return Task1Result(
                success=False,
                data={"error": str(exc)},
                message="Task 1 encountered an error"
            )

def run_task1() -> Task1Result:
    """Convenient function to run Task 1 without instantiating the class.

    Returns
    -------
    Task1Result
        The outcome of the task execution.
    """
    runner = Task1Runner()
    return runner.run()
