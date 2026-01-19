"""
Forbidden phrases hard check.
"""
from typing import List
from .base import HardCheck
from ..models import HardCheckResult, Case


class ForbiddenPhrasesCheck(HardCheck):
    """Check if output contains forbidden phrases."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.phrases = self.config.get('phrases', [])
        self.case_insensitive = self.config.get('case_insensitive', True)

    def applies_to(self, case: Case) -> bool:
        """Always applies to all cases."""
        return True

    def check(self, output: str, case: Case) -> HardCheckResult:
        """
        Check if output contains forbidden phrases.

        Args:
            output: Candidate output
            case: Case being checked

        Returns:
            HardCheckResult
        """
        found_phrases = []

        for phrase in self.phrases:
            if self.case_insensitive:
                if phrase.lower() in output.lower():
                    found_phrases.append(phrase)
            else:
                if phrase in output:
                    found_phrases.append(phrase)

        passed = len(found_phrases) == 0

        if passed:
            return HardCheckResult(
                name="forbidden_phrases",
                passed=True,
                severity="error",
                reason=None,
                details={"checked_phrases": self.phrases}
            )
        else:
            return HardCheckResult(
                name="forbidden_phrases",
                passed=False,
                severity="error",
                reason=f"Output contains forbidden phrases: {', '.join(found_phrases)}",
                details={
                    "found_phrases": found_phrases,
                    "checked_phrases": self.phrases
                }
            )
