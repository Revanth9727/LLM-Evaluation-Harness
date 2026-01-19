"""
Metrics calculation for evaluation runs.
"""
import numpy as np
from typing import List, Dict, Any, Tuple, Optional


def calculate_win_rate(judge_votes: List[Dict[str, Any]]) -> Optional[float]:
    """
    Calculate win rate: A_wins / (A_wins + B_wins + ties).
    Ignores 'uncertain' votes.

    Args:
        judge_votes: List of judge vote dictionaries

    Returns:
        Win rate as float, or None if no valid votes
    """
    if not judge_votes:
        return None

    # Filter out uncertain votes
    valid_votes = [v for v in judge_votes if v.get('winner') != 'uncertain']

    if not valid_votes:
        return None

    a_wins = sum(1 for v in valid_votes if v.get('winner') == 'A')
    total_valid = len(valid_votes)

    if total_valid == 0:
        return None

    return a_wins / total_valid


def calculate_refusal_rate(
    outputs: Dict[str, Dict[str, Any]],
    canonical_idk: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate refusal rate per candidate.
    Refusal = output empty OR output == canonical_idk OR error present.

    Args:
        outputs: Dict of {case_id: {"A": CandidateOutput, "B": CandidateOutput}}
        canonical_idk: The canonical "I don't know" string

    Returns:
        Dict with 'candidate_a' and 'candidate_b' refusal rates
    """
    if not outputs:
        return {'candidate_a': 0.0, 'candidate_b': 0.0}

    total_cases = len(outputs)
    a_refusals = 0
    b_refusals = 0

    for case_id, case_outputs in outputs.items():
        # Check A
        a_output = case_outputs.get('A')
        if a_output:
            output_text = a_output.output if hasattr(a_output, 'output') else a_output.get('output', '')
            error = a_output.error if hasattr(a_output, 'error') else a_output.get('error')

            if not output_text or error:
                a_refusals += 1
            elif canonical_idk and output_text.strip() == canonical_idk.strip():
                a_refusals += 1

        # Check B
        b_output = case_outputs.get('B')
        if b_output:
            output_text = b_output.output if hasattr(b_output, 'output') else b_output.get('output', '')
            error = b_output.error if hasattr(b_output, 'error') else b_output.get('error')

            if not output_text or error:
                b_refusals += 1
            elif canonical_idk and output_text.strip() == canonical_idk.strip():
                b_refusals += 1

    return {
        'candidate_a': a_refusals / total_cases if total_cases > 0 else 0.0,
        'candidate_b': b_refusals / total_cases if total_cases > 0 else 0.0
    }


def calculate_format_pass_rate(
    hard_checks: Dict[str, Dict[str, List[Any]]]
) -> Dict[str, float]:
    """
    Calculate format check pass rate per candidate.
    Pass = all error-level checks passed.

    Args:
        hard_checks: Dict of {case_id: {"A": [results], "B": [results]}}

    Returns:
        Dict with 'candidate_a' and 'candidate_b' pass rates
    """
    if not hard_checks:
        return {'candidate_a': 1.0, 'candidate_b': 1.0}

    total_cases = len(hard_checks)
    a_passes = 0
    b_passes = 0

    for case_id, case_checks in hard_checks.items():
        # Check A
        a_results = case_checks.get('A', [])
        if all(r.passed for r in a_results if (hasattr(r, 'severity') and r.severity == 'error')):
            a_passes += 1

        # Check B
        b_results = case_checks.get('B', [])
        if all(r.passed for r in b_results if (hasattr(r, 'severity') and r.severity == 'error')):
            b_passes += 1

    return {
        'candidate_a': a_passes / total_cases if total_cases > 0 else 1.0,
        'candidate_b': b_passes / total_cases if total_cases > 0 else 1.0
    }


def bootstrap_ci(
    values: List[float],
    n_resamples: int = 1000,
    ci_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval using percentile method.

    Args:
        values: List of binary values (0 or 1) for bootstrap
        n_resamples: Number of bootstrap resamples (default 1000)
        ci_level: Confidence level (default 0.95 for 95% CI)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if not values or len(values) < 2:
        return (0.0, 0.0)

    values_array = np.array(values)
    n = len(values_array)

    # Generate bootstrap samples
    bootstrap_means = []
    rng = np.random.RandomState(1337)  # Fixed seed for reproducibility

    for _ in range(n_resamples):
        # Resample with replacement
        sample = rng.choice(values_array, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))

    # Calculate percentiles
    alpha = 1 - ci_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100

    lower = np.percentile(bootstrap_means, lower_percentile)
    upper = np.percentile(bootstrap_means, upper_percentile)

    return (float(lower), float(upper))


def get_win_rate_samples(judge_votes: List[Dict[str, Any]]) -> List[float]:
    """
    Convert judge votes to binary samples for bootstrap.
    1 if A wins, 0 otherwise (B wins or tie).
    Ignores uncertain votes.

    Args:
        judge_votes: List of judge vote dictionaries

    Returns:
        List of binary values (0 or 1)
    """
    samples = []
    for vote in judge_votes:
        winner = vote.get('winner')
        if winner == 'uncertain':
            continue  # Skip uncertain
        if winner == 'A':
            samples.append(1.0)
        else:  # B or tie
            samples.append(0.0)

    return samples
