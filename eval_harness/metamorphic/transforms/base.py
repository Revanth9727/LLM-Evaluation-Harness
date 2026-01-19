"""
Base transform interface.
"""
from abc import ABC, abstractmethod
from ...models import Case


class Transform(ABC):
    """Base class for transforms."""

    def __init__(self, config: dict = None):
        """
        Initialize transform.

        Args:
            config: Transform-specific configuration
        """
        self.config = config or {}

    @abstractmethod
    def transform(self, case: Case) -> Case:
        """
        Transform a case.

        Args:
            case: Original case

        Returns:
            Transformed case
        """
        pass
