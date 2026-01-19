"""
Mock judge provider for testing without API calls.
"""
import json
from .base import BaseProvider


class MockJudgeProvider(BaseProvider):
    """
    Mock judge provider that returns deterministic judge responses.
    Always returns 'tie' with confidence 0.0 for CI/testing.
    """

    def __init__(self, model: str = "mock_judge", **kwargs):
        super().__init__(model, **kwargs)

    def generate(self, prompt: str, system_message: str = None, **kwargs) -> str:
        """
        Generate a mock judge response.

        Args:
            prompt: Judge prompt (ignored)
            system_message: System message (ignored)
            **kwargs: Additional parameters (ignored)

        Returns:
            Deterministic JSON response
        """
        # Return a valid judge response in JSON format
        response = {
            "winner": "tie",
            "confidence": 0.0,
            "reasons": ["Mock judge always returns tie"],
            "citations_assessed": [],
            "notes": "Deterministic mock response for testing"
        }

        return json.dumps(response, indent=2)
