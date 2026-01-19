"""
Base provider interface.
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, model: str, **kwargs):
        """
        Initialize provider.

        Args:
            model: Model identifier
            **kwargs: Additional provider-specific parameters
        """
        self.model = model
        self.kwargs = kwargs

    @abstractmethod
    def generate(self, prompt: str, system_message: str = None, **kwargs) -> str:
        """
        Generate a response from the model.

        Args:
            prompt: Input prompt (user message)
            system_message: Optional system message/instructions
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        pass
