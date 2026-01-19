"""
OpenAI provider (also supports OpenAI-compatible APIs).
"""
import os
from typing import Optional
from openai import OpenAI
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """
    OpenAI provider.
    Also supports OpenAI-compatible APIs via base_url parameter.
    """

    def __init__(self, model: str, **kwargs):
        super().__init__(model, **kwargs)

        # Get API key and base URL from kwargs or environment
        api_key = kwargs.get('api_key')
        if api_key is None:
            api_key = os.getenv('OPENAI_API_KEY')

        base_url = kwargs.get('base_url')
        if base_url is None:
            base_url = os.getenv('OPENAI_BASE_URL')

        # For local servers, API key might be empty/not required
        # Only enforce API key requirement if not using a custom base_url
        if not api_key and not base_url:
            raise ValueError("OPENAI_API_KEY must be set in environment or passed as api_key parameter")

        # Initialize client
        # Use dummy key for local servers if api_key is empty
        if not api_key:
            api_key = "sk-no-key-required"

        client_kwargs = {'api_key': api_key}
        if base_url:
            client_kwargs['base_url'] = base_url

        self.client = OpenAI(**client_kwargs)
        self.temperature = kwargs.get('temperature', 0.0)
        self.max_tokens = kwargs.get('max_tokens', 2000)

    def generate(self, prompt: str, system_message: str = None, **kwargs) -> str:
        """
        Generate a response using OpenAI API.

        Args:
            prompt: Input prompt (user message)
            system_message: Optional system message/instructions
            **kwargs: Override generation parameters

        Returns:
            Generated text
        """
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)

        # Build messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content
