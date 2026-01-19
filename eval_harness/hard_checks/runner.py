"""
Hard check runner.
"""
from typing import List, Dict, Any, Optional
from .base import HardCheck
from .non_empty import NonEmptyCheck
from .citations_present import CitationsPresentCheck
from .canonical_idk import CanonicalIDKCheck
from .max_length import MaxLengthCheck
from .forbidden_phrases import ForbiddenPhrasesCheck
from .latency_budget import LatencyBudgetCheck
from .cost_proxy import CostProxyCheck
from ..models import HardCheckResult, Case


class HardCheckRunner:
    """Runs all applicable hard checks."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize hard check runner.

        Args:
            config: Hard checks configuration
        """
        self.config = config
        self.enabled = config.get('enabled', True)

        # Initialize checks
        task_contract = config.get('task_contract', {})
        self.checks: List[HardCheck] = [
            NonEmptyCheck(),
            CitationsPresentCheck(task_contract),
            CanonicalIDKCheck(task_contract)
        ]

        # Add optional checks if configured
        if 'max_length' in config:
            self.checks.append(MaxLengthCheck(config['max_length']))

        if 'forbidden_phrases' in config:
            self.checks.append(ForbiddenPhrasesCheck(config['forbidden_phrases']))

        if 'latency_budget' in config:
            self.latency_check = LatencyBudgetCheck(config['latency_budget'])
            self.checks.append(self.latency_check)
        else:
            self.latency_check = None

        if 'cost_proxy' in config:
            self.checks.append(CostProxyCheck(config['cost_proxy']))

    def run_checks(self, output: str, case: Case, latency_ms: Optional[float] = None) -> List[HardCheckResult]:
        """
        Run all applicable hard checks on an output.

        Args:
            output: Model output to check
            case: Case being evaluated
            latency_ms: Generation latency in milliseconds (for latency budget check)

        Returns:
            List of HardCheckResult objects
        """
        if not self.enabled:
            return []

        results = []
        for check in self.checks:
            if check.applies_to(case):
                # Pass latency_ms to latency budget check
                if isinstance(check, LatencyBudgetCheck):
                    result = check.check(output, case, latency_ms=latency_ms)
                else:
                    result = check.check(output, case)
                results.append(result)

        return results

    def has_failures(self, results: List[HardCheckResult]) -> bool:
        """
        Check if any hard checks failed.

        Args:
            results: List of check results

        Returns:
            True if any error-level check failed
        """
        return any(
            not r.passed and r.severity == "error"
            for r in results
        )
