"""
System prompt loader utility.
"""
from pathlib import Path
from typing import Optional


def load_system_prompt(prompt_path: Optional[str]) -> Optional[str]:
    """
    Load system prompt from file.

    Args:
        prompt_path: Path to system prompt file (None to skip)

    Returns:
        System prompt text, or None if path not provided

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    if not prompt_path:
        return None

    path = Path(prompt_path)
    if not path.exists():
        raise FileNotFoundError(f"System prompt not found: {prompt_path}")

    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()
