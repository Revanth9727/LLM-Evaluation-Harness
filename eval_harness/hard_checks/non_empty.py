"""
Non-empty output check.
"""
from .base import HardCheck
from ..models import HardCheckResult, Case


class NonEmptyCheck(HardCheck):
    """Check that output is not empty."""

    def applies_to(self, case: Case) -> bool:
        """Always applies."""
        return True

    def check(self, output: str, case: Case) -> HardCheckResult:
        """
        Check if output is non-empty.

        Args:
            output: Model output
            case: Case being evaluated

        Returns:
            HardCheckResult
        """
        is_empty = not output or not output.strip()

        return HardCheckResult(
            name="non_empty",
            passed=not is_empty,
            severity="error",
            reason="empty_output" if is_empty else None,
            details={
                "output_length": len(output),
                "output_stripped_length": len(output.strip()) if output else 0
            }
        )
