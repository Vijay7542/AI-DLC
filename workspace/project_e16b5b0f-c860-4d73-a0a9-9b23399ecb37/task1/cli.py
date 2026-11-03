"""Command‑line interface for Task 1.

The CLI is intentionally lightweight and uses the standard library ``argparse``
module to avoid external dependencies. It demonstrates how the :class:`Task1Processor`
can be wired into a script entry point.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .processor import Task1Processor, Task1Result

logger = logging.getLogger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="task1",
        description="Execute Task 1 and output the result as JSON.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Write the JSON result to the given file instead of stdout.",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging verbosity.",
    )
    return parser.parse_args(argv)


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def _result_to_dict(result: Task1Result) -> dict:
    return {
        "success": result.success,
        "data": result.data,
        "messages": result.messages,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _configure_logging(args.log_level)

    processor = Task1Processor()
    result = processor.run()

    result_dict = _result_to_dict(result)
    json_output = json.dumps(result_dict, indent=2, ensure_ascii=False)

    if args.output:
        try:
            args.output.write_text(json_output + "\n", encoding="utf-8")
            logger.info("Result written to %s", args.output)
        except OSError as exc:
            logger.error("Failed to write output file %s: %s", args.output, exc)
            return 1
    else:
        sys.stdout.write(json_output + "\n")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
