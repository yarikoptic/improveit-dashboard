"""Markdown utilities for safe rendering."""


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
