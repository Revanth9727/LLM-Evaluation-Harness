"""
Canonical IDK check.
"""
from .base import HardCheck
from ..models import HardCheckResult, Case


class CanonicalIDKCheck(HardCheck):
    """Check that output is exactly the canonical IDK string."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        # Default canonical IDK from CONTRACT_CONSTANTS.md
        self.canonical_idk = self.config.get(
            'canonical_idk',
            "I don't know based on the provided context."
        )

    def applies_to(self, case: Case) -> bool:
        """
        Check if canonical IDK is required for this case.

        Applies when:
        - expected_behavior == "no_answer" OR
        - tags contains "should_say_idk" OR
        - tags contains "missing_context_expected"
        """
        if case.expected_behavior == "no_answer":
            return True

        if case.tags:
            if "should_say_idk" in case.tags:
                return True
            if "missing_context_expected" in case.tags:
                return True

        return False

    def check(self, output: str, case: Case) -> HardCheckResult:
        """
        Check if output is exactly the canonical IDK string.

        Args:
            output: Model output
            case: Case being evaluated

        Returns:
            HardCheckResult
        """
        # Exact match required (strip whitespace for comparison)
        output_stripped = output.strip()
        is_exact_match = output_stripped == self.canonical_idk

        return HardCheckResult(
            name="canonical_idk",
            passed=is_exact_match,
            severity="error",
            reason="incorrect_idk" if not is_exact_match else None,
            details={
                "expected": self.canonical_idk,
                "actual": output_stripped,
                "match": is_exact_match
            }
        )
