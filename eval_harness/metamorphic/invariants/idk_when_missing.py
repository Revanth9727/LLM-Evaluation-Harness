"""
IDK when context missing invariant.
"""
from .base import Invariant
from ...models import Case


class IDKWhenMissingInvariant(Invariant):
    """When key context is removed, output should be canonical IDK."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.canonical_idk = self.config.get(
            'canonical_idk',
            "I don't know based on the provided context."
        )

    def check(
        self,
        original_case: Case,
        transformed_case: Case,
        original_output: str,
        transformed_output: str
    ) -> bool:
        """
        Check if IDK when context missing.

        Args:
            original_case: Original case
            transformed_case: Transformed case
            original_output: Output for original case
            transformed_output: Output for transformed case

        Returns:
            True if transformed output is canonical IDK, False otherwise
        """
        # Only check if transformed case expects IDK
        if transformed_case.expected_behavior == "no_answer" or \
           (transformed_case.tags and "should_say_idk" in transformed_case.tags):
            return transformed_output.strip() == self.canonical_idk

        # Invariant doesn't apply
        return True
