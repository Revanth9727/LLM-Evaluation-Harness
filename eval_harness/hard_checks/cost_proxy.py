"""
Cost proxy hard check.
"""
from .base import HardCheck
from ..models import HardCheckResult, Case


class CostProxyCheck(HardCheck):
    """Check if estimated cost is within budget."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.max_tokens = self.config.get('max_tokens', 2000)
        # Approximate 1 token = 4 characters (rough estimate for English)
        self.chars_per_token = self.config.get('chars_per_token', 4)

    def applies_to(self, case: Case) -> bool:
        """Always applies to all cases."""
        return True

    def check(self, output: str, case: Case) -> HardCheckResult:
        """
        Check if estimated token cost is within budget.

        Args:
            output: Candidate output
            case: Case being checked

        Returns:
            HardCheckResult
        """
        # Estimate tokens from character count
        estimated_tokens = len(output) // self.chars_per_token
        passed = estimated_tokens <= self.max_tokens

        if passed:
            return HardCheckResult(
                name="cost_proxy",
                passed=True,
                severity="error",
                reason=None,
                details={
                    "estimated_tokens": estimated_tokens,
                    "limit_tokens": self.max_tokens,
                    "chars": len(output)
                }
            )
        else:
            return HardCheckResult(
                name="cost_proxy",
                passed=False,
                severity="error",
                reason=f"Estimated tokens {estimated_tokens} exceeds budget {self.max_tokens}",
                details={
                    "estimated_tokens": estimated_tokens,
                    "limit_tokens": self.max_tokens,
                    "chars": len(output)
                }
            )
