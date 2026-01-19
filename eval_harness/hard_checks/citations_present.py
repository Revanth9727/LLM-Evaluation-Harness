"""
Citations present check.
"""
import re
from .base import HardCheck
from ..models import HardCheckResult, Case


class CitationsPresentCheck(HardCheck):
    """Check that required citations are present."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        # Default citation regex from CONTRACT_CONSTANTS.md
        self.citation_regex = self.config.get(
            'citation_regex',
            r'\[[A-Za-z0-9_-]+(?:\s+p|_p)\d+\]'
        )
        self.pattern = re.compile(self.citation_regex)

    def applies_to(self, case: Case) -> bool:
        """
        Check if citations are required for this case.

        Applies when:
        - expected_behavior == "answer_with_citations" OR
        - tags contains "requires_citations"
        """
        if case.expected_behavior == "answer_with_citations":
            return True

        if case.tags and "requires_citations" in case.tags:
            return True

        return False

    def check(self, output: str, case: Case) -> HardCheckResult:
        """
        Check if citations are present.

        Args:
            output: Model output
            case: Case being evaluated

        Returns:
            HardCheckResult
        """
        citations = self.pattern.findall(output)
        has_citations = len(citations) > 0

        return HardCheckResult(
            name="citations_present",
            passed=has_citations,
            severity="error",
            reason="missing_citations" if not has_citations else None,
            details={
                "expected": "at least one citation marker",
                "found": citations,
                "count": len(citations)
            }
        )
