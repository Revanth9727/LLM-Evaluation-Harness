"""
Tests for metrics calculation.
"""
import pytest
from eval_harness.metrics import (
    calculate_win_rate,
    calculate_refusal_rate,
    calculate_format_pass_rate,
    bootstrap_ci,
    get_win_rate_samples
)


class MockCandidateOutput:
    """Mock candidate output for testing."""
    def __init__(self, output: str, error: str = None, latency_ms: float = None):
        self.output = output
        self.error = error
        self.latency_ms = latency_ms


class MockHardCheckResult:
    """Mock hard check result for testing."""
    def __init__(self, name: str, passed: bool, severity: str = 'error'):
        self.name = name
        self.passed = passed
        self.severity = severity


def test_calculate_win_rate_basic():
    """Test basic win rate calculation."""
    votes = [
        {'case_id': 'c1', 'winner': 'A'},
        {'case_id': 'c2', 'winner': 'B'},
        {'case_id': 'c3', 'winner': 'A'},
        {'case_id': 'c4', 'winner': 'tie'},
    ]
    win_rate = calculate_win_rate(votes)
    assert win_rate == 0.5  # 2 A wins out of 4 total


def test_calculate_win_rate_ignore_uncertain():
    """Test that uncertain votes are ignored."""
    votes = [
        {'case_id': 'c1', 'winner': 'A'},
        {'case_id': 'c2', 'winner': 'B'},
        {'case_id': 'c3', 'winner': 'uncertain'},
        {'case_id': 'c4', 'winner': 'uncertain'},
    ]
    win_rate = calculate_win_rate(votes)
    assert win_rate == 0.5  # 1 A win out of 2 valid votes


def test_calculate_win_rate_empty():
    """Test win rate with empty votes."""
    assert calculate_win_rate([]) is None


def test_calculate_win_rate_all_uncertain():
    """Test win rate with all uncertain votes."""
    votes = [
        {'case_id': 'c1', 'winner': 'uncertain'},
        {'case_id': 'c2', 'winner': 'uncertain'},
    ]
    assert calculate_win_rate(votes) is None


def test_calculate_refusal_rate_empty_output():
    """Test refusal detection with empty output."""
    outputs = {
        'c1': {
            'A': MockCandidateOutput(''),
            'B': MockCandidateOutput('Answer')
        }
    }
    rates = calculate_refusal_rate(outputs)
    assert rates['candidate_a'] == 1.0
    assert rates['candidate_b'] == 0.0


def test_calculate_refusal_rate_canonical_idk():
    """Test refusal detection with canonical IDK."""
    canonical_idk = "I don't know based on the provided context."
    outputs = {
        'c1': {
            'A': MockCandidateOutput(canonical_idk),
            'B': MockCandidateOutput('Answer')
        }
    }
    rates = calculate_refusal_rate(outputs, canonical_idk)
    assert rates['candidate_a'] == 1.0
    assert rates['candidate_b'] == 0.0


def test_calculate_refusal_rate_error():
    """Test refusal detection with error."""
    outputs = {
        'c1': {
            'A': MockCandidateOutput('', error='API error'),
            'B': MockCandidateOutput('Answer')
        }
    }
    rates = calculate_refusal_rate(outputs)
    assert rates['candidate_a'] == 1.0
    assert rates['candidate_b'] == 0.0


def test_calculate_refusal_rate_mixed():
    """Test refusal rate with mixed outputs."""
    canonical_idk = "I don't know based on the provided context."
    outputs = {
        'c1': {'A': MockCandidateOutput('Answer'), 'B': MockCandidateOutput('Answer')},
        'c2': {'A': MockCandidateOutput(''), 'B': MockCandidateOutput('Answer')},
        'c3': {'A': MockCandidateOutput(canonical_idk), 'B': MockCandidateOutput('Answer')},
        'c4': {'A': MockCandidateOutput('Answer'), 'B': MockCandidateOutput('')},
    }
    rates = calculate_refusal_rate(outputs, canonical_idk)
    assert rates['candidate_a'] == 0.5  # 2 refusals out of 4
    assert rates['candidate_b'] == 0.25  # 1 refusal out of 4


def test_calculate_format_pass_rate_all_pass():
    """Test format pass rate with all passing."""
    hard_checks = {
        'c1': {
            'A': [MockHardCheckResult('check1', True)],
            'B': [MockHardCheckResult('check1', True)]
        }
    }
    rates = calculate_format_pass_rate(hard_checks)
    assert rates['candidate_a'] == 1.0
    assert rates['candidate_b'] == 1.0


def test_calculate_format_pass_rate_some_fail():
    """Test format pass rate with some failures."""
    hard_checks = {
        'c1': {
            'A': [MockHardCheckResult('check1', False, 'error')],
            'B': [MockHardCheckResult('check1', True, 'error')]
        },
        'c2': {
            'A': [MockHardCheckResult('check1', True, 'error')],
            'B': [MockHardCheckResult('check1', True, 'error')]
        }
    }
    rates = calculate_format_pass_rate(hard_checks)
    assert rates['candidate_a'] == 0.5  # 1 pass out of 2
    assert rates['candidate_b'] == 1.0  # 2 passes out of 2


def test_calculate_format_pass_rate_ignore_warnings():
    """Test that warnings don't affect pass rate."""
    hard_checks = {
        'c1': {
            'A': [
                MockHardCheckResult('check1', True, 'error'),
                MockHardCheckResult('warn1', False, 'warning')  # Warning failure ignored
            ],
            'B': [MockHardCheckResult('check1', True, 'error')]
        }
    }
    rates = calculate_format_pass_rate(hard_checks)
    assert rates['candidate_a'] == 1.0  # Error-level check passed
    assert rates['candidate_b'] == 1.0


def test_bootstrap_ci_basic():
    """Test basic bootstrap CI calculation."""
    values = [1, 1, 0, 1, 0, 1, 1, 0, 1, 1]  # 70% success
    lower, upper = bootstrap_ci(values, n_resamples=1000, ci_level=0.95)

    # CI should contain the true mean (0.7)
    assert lower < 0.7 < upper
    # CI should be reasonable (lower < upper)
    assert lower < upper
    assert 0.0 <= lower <= 1.0
    assert 0.0 <= upper <= 1.0


def test_bootstrap_ci_empty():
    """Test bootstrap CI with empty values."""
    lower, upper = bootstrap_ci([])
    assert lower == 0.0
    assert upper == 0.0


def test_bootstrap_ci_single_value():
    """Test bootstrap CI with single value."""
    lower, upper = bootstrap_ci([1])
    assert lower == 0.0
    assert upper == 0.0


def test_get_win_rate_samples():
    """Test conversion of judge votes to binary samples."""
    votes = [
        {'winner': 'A'},
        {'winner': 'B'},
        {'winner': 'A'},
        {'winner': 'tie'},
        {'winner': 'uncertain'},  # Should be ignored
    ]
    samples = get_win_rate_samples(votes)
    assert samples == [1.0, 0.0, 1.0, 0.0]  # uncertain excluded


def test_get_win_rate_samples_empty():
    """Test with empty votes."""
    samples = get_win_rate_samples([])
    assert samples == []
