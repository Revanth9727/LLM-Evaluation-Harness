"""
Latency budget hard check.
"""
from .base import HardCheck
from ..models import HardCheckResult, Case


class LatencyBudgetCheck(HardCheck):
    """Check if generation latency is within budget."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.max_latency_ms = self.config.get('max_latency_ms', 10000)

    def applies_to(self, case: Case) -> bool:
        """Always applies to all cases."""
        return True

    def check(self, output: str, case: Case, latency_ms: float = None) -> HardCheckResult:
        """
        Check if latency is within budget.

        Args:
            output: Candidate output
            case: Case being checked
            latency_ms: Measured latency in milliseconds

        Returns:
            HardCheckResult
        """
        if latency_ms is None:
            # If no latency provided, pass by default
            return HardCheckResult(
                name="latency_budget",
                passed=True,
                severity="warning",
                reason=None,
                details={"latency_ms": None, "limit_ms": self.max_latency_ms}
            )

        passed = latency_ms <= self.max_latency_ms

        if passed:
            return HardCheckResult(
                name="latency_budget",
                passed=True,
                severity="error",
                reason=None,
                details={"latency_ms": latency_ms, "limit_ms": self.max_latency_ms}
            )
        else:
            return HardCheckResult(
                name="latency_budget",
                passed=False,
                severity="error",
                reason=f"Latency {latency_ms:.0f}ms exceeds budget {self.max_latency_ms}ms",
                details={"latency_ms": latency_ms, "limit_ms": self.max_latency_ms}
            )
