"""
Citations present invariant.
"""
import re
from .base import Invariant
from ...models import Case


class CitationsPresentInvariant(Invariant):
    """If original had citations, transformed should too."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.citation_regex = self.config.get(
            'citation_regex',
            r'\[[A-Za-z0-9_-]+(?:\s+p|_p)\d+\]'
        )
        self.pattern = re.compile(self.citation_regex)

    def check(
        self,
        original_case: Case,
        transformed_case: Case,
        original_output: str,
        transformed_output: str
    ) -> bool:
        """
        Check if citations are preserved.

        Args:
            original_case: Original case
            transformed_case: Transformed case
            original_output: Output for original case
            transformed_output: Output for transformed case

        Returns:
            True if citations preserved (or not required), False otherwise
        """
        # Check if original had citations
        original_citations = self.pattern.findall(original_output)

        # If original didn't have citations, invariant doesn't apply
        if not original_citations:
            return True

        # Check if transformed has citations
        transformed_citations = self.pattern.findall(transformed_output)

        return len(transformed_citations) > 0
