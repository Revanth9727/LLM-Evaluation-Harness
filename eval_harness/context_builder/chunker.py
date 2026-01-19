"""
Text chunking utilities.
"""


def truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    """
    Truncate text if it exceeds max_chars.

    Args:
        text: Text to truncate
        max_chars: Maximum characters

    Returns:
        Tuple of (truncated_text, was_truncated)
    """
    if len(text) <= max_chars:
        return text, False

    truncated = text[:max_chars] + "...[TRUNCATED]"
    return truncated, True
