"""
Base invariant interface.
"""
from abc import ABC, abstractmethod
from ...models import Case


class Invariant(ABC):
    """Base class for invariants."""

    def __init__(self, config: dict = None):
        """
        Initialize invariant.

        Args:
            config: Invariant-specific configuration
        """
        self.config = config or {}

    @abstractmethod
    def check(
        self,
        original_case: Case,
        transformed_case: Case,
        original_output: str,
        transformed_output: str
    ) -> bool:
        """
        Check if invariant holds.

        Args:
            original_case: Original case
            transformed_case: Transformed case
            original_output: Output for original case
            transformed_output: Output for transformed case

        Returns:
            True if invariant holds, False otherwise
        """
        pass
