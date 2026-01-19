"""
Base hard check interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..models import HardCheckResult, Case


class HardCheck(ABC):
    """Base class for hard checks."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize hard check.

        Args:
            config: Check-specific configuration
        """
        self.config = config or {}

    @abstractmethod
    def applies_to(self, case: Case) -> bool:
        """
        Check if this hard check applies to the given case.

        Args:
            case: Case to check

        Returns:
            True if check applies, False otherwise
        """
        pass

    @abstractmethod
    def check(self, output: str, case: Case) -> HardCheckResult:
        """
        Run the hard check on an output.

        Args:
            output: Model output to check
            case: Case being evaluated

        Returns:
            HardCheckResult with pass/fail and details
        """
        pass
