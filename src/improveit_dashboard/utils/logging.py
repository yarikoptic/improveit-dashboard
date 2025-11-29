"""Logging configuration for improveit-dashboard."""

import logging
import sys
from typing import TextIO


def setup_logging(
    level: int = logging.INFO,
    stream: TextIO = sys.stderr,
) -> None:
    """Configure logging for the application.

    Args:
        level: Log level (default: INFO)
        stream: Output stream (default: stderr)
    """
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure handler
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    # Configure root logger for our package
    logger = logging.getLogger("improveit_dashboard")
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
