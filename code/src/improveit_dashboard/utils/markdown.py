"""Markdown utilities for safe rendering."""

import re
from pathlib import Path

from improveit_dashboard.utils.logging import get_logger

logger = get_logger(__name__)

# Pattern to match the "Last updated" line
LAST_UPDATED_PATTERN = re.compile(r"^\*Last updated: .+\*$", re.MULTILINE)


def sanitize_for_table(text: str) -> str:
    """Sanitize text for safe inclusion in markdown table cells.

    GitHub comments may contain markdown that breaks table formatting:
    - Newlines break table rows
    - Pipe characters break table columns
    - Blockquotes, lists, etc. cause unintended rendering

    Args:
        text: Raw text (may contain markdown/newlines)

    Returns:
        Sanitized text safe for table cells
    """
    # Replace various newline formats with spaces
    text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")

    # Escape pipe characters (table column separator)
    text = text.replace("|", "\\|")

    # Collapse multiple spaces into one
    text = " ".join(text.split())

    return text.strip()


def truncate(text: str, max_len: int) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def sanitize_and_truncate(text: str, max_len: int) -> str:
    """Sanitize text for table cells and truncate to max length.

    Args:
        text: Raw text (may contain markdown/newlines)
        max_len: Maximum length after sanitization

    Returns:
        Sanitized and truncated text
    """
    return truncate(sanitize_for_table(text), max_len)


def _strip_last_updated(content: str) -> str:
    """Remove the 'Last updated' line from content for comparison."""
    return LAST_UPDATED_PATTERN.sub("", content)


def write_if_changed(path: Path, content: str) -> bool:
    """Write content to file only if there are meaningful changes.

    Ignores changes that only affect the 'Last updated' timestamp line.
    This keeps git commits focused on actual content changes.

    Args:
        path: Path to write to
        content: New content to write

    Returns:
        True if file was written, False if skipped (no meaningful changes)
    """
    if path.exists():
        existing = path.read_text()
        # Compare content ignoring the "Last updated" line
        if _strip_last_updated(existing) == _strip_last_updated(content):
            logger.debug(f"Skipping {path} (only timestamp changed)")
            return False

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True
