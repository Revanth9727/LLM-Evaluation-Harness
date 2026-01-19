"""
Provider factory.
"""
from typing import Dict, Any
from .base import BaseProvider
from .mock_provider import MockProvider
from .mock_judge import MockJudgeProvider
from .openai_provider import OpenAIProvider


def create_provider(provider_type: str, model: str, **kwargs) -> BaseProvider:
    """
    Create a provider instance.

    Args:
        provider_type: Provider type ("openai", "mock", etc.)
        model: Model identifier
        **kwargs: Provider-specific parameters

    Returns:
        Provider instance

    Raises:
        ValueError: If provider type is unknown
    """
    provider_type = provider_type.lower()

    if provider_type == "mock":
        return MockProvider(model, **kwargs)
    elif provider_type == "mock_judge":
        return MockJudgeProvider(model, **kwargs)
    elif provider_type == "openai":
        return OpenAIProvider(model, **kwargs)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
