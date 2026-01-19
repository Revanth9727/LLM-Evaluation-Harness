"""
Mock provider for testing without API keys.
"""
from .base import BaseProvider


class MockProvider(BaseProvider):
    """Mock provider that returns deterministic responses."""

    def __init__(self, model: str = "mock", **kwargs):
        super().__init__(model, **kwargs)
        self.response_template = kwargs.get(
            'response_template',
            "This is a mock response to: {prompt_preview}"
        )

    def generate(self, prompt: str, system_message: str = None, **kwargs) -> str:
        """
        Generate a mock response.

        Args:
            prompt: Input prompt
            system_message: Optional system message (ignored by mock)
            **kwargs: Ignored

        Returns:
            Mock response
        """
        # Create deterministic response based on prompt
        prompt_preview = prompt[:50].replace('\n', ' ')

        # If prompt asks about something specific, try to give a reasonable mock answer
        if "don't know" in prompt.lower() or "cannot answer" in prompt.lower():
            return "I don't know based on the provided context."

        # Check if this looks like a question that should have citations
        if any(marker in prompt for marker in ['[', 'p', 'doc']):
            # Include a mock citation
            return f"Based on the provided context, this is a mock answer. [DOC p1]"

        return self.response_template.format(prompt_preview=prompt_preview)
