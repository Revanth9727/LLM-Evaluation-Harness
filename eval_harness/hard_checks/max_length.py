"""
Max length hard check.
"""
from .base import HardCheck
from ..models import HardCheckResult, Case


class MaxLengthCheck(HardCheck):
    """Check if output exceeds maximum character length."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.max_chars = self.config.get('max_chars', 3000)

    def applies_to(self, case: Case) -> bool:
        """Always applies to all cases."""
        return True

    def check(self, output: str, case: Case) -> HardCheckResult:
        """
        Check if output length is within limit.

        Args:
            output: Candidate output
            case: Case being checked

        Returns:
            HardCheckResult
        """
        output_length = len(output)
        passed = output_length <= self.max_chars

        if passed:
            return HardCheckResult(
                name="max_length",
                passed=True,
                severity="error",
                reason=None,
                details={"length": output_length, "limit": self.max_chars}
            )
        else:
            return HardCheckResult(
                name="max_length",
                passed=False,
                severity="error",
                reason=f"Output length {output_length} exceeds limit {self.max_chars}",
                details={"length": output_length, "limit": self.max_chars}
            )
