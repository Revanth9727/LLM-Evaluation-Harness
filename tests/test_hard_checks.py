"""
Tests for hard checks.
"""
import pytest
from eval_harness.models import Case
from eval_harness.hard_checks.non_empty import NonEmptyCheck
from eval_harness.hard_checks.citations_present import CitationsPresentCheck
from eval_harness.hard_checks.canonical_idk import CanonicalIDKCheck


def test_non_empty_check_pass():
    """Test non-empty check passes with valid output."""
    check = NonEmptyCheck()
    case = Case(id="test", input="question")
    result = check.check("Valid output", case)
    assert result.passed


def test_non_empty_check_fail():
    """Test non-empty check fails with empty output."""
    check = NonEmptyCheck()
    case = Case(id="test", input="question")
    result = check.check("", case)
    assert not result.passed


def test_citations_present_check_applies():
    """Test citations check applies correctly."""
    check = CitationsPresentCheck()

    # Should apply when expected_behavior is answer_with_citations
    case1 = Case(id="test", input="q", expected_behavior="answer_with_citations")
    assert check.applies_to(case1)

    # Should apply when tag is requires_citations
    case2 = Case(id="test", input="q", tags=["requires_citations"])
    assert check.applies_to(case2)

    # Should not apply otherwise
    case3 = Case(id="test", input="q")
    assert not check.applies_to(case3)


def test_citations_present_check_pass():
    """Test citations check passes with valid citation."""
    check = CitationsPresentCheck()
    case = Case(id="test", input="q", expected_behavior="answer_with_citations")
    result = check.check("Answer with [DOC p5] citation.", case)
    assert result.passed


def test_citations_present_check_fail():
    """Test citations check fails without citation."""
    check = CitationsPresentCheck()
    case = Case(id="test", input="q", expected_behavior="answer_with_citations")
    result = check.check("Answer without citation.", case)
    assert not result.passed


def test_canonical_idk_check_applies():
    """Test canonical IDK check applies correctly."""
    check = CanonicalIDKCheck()

    # Should apply when expected_behavior is no_answer
    case1 = Case(id="test", input="q", expected_behavior="no_answer")
    assert check.applies_to(case1)

    # Should apply when tag is should_say_idk
    case2 = Case(id="test", input="q", tags=["should_say_idk"])
    assert check.applies_to(case2)


def test_canonical_idk_check_pass():
    """Test canonical IDK check passes with exact match."""
    check = CanonicalIDKCheck()
    case = Case(id="test", input="q", expected_behavior="no_answer")
    result = check.check("I don't know based on the provided context.", case)
    assert result.passed


def test_canonical_idk_check_fail():
    """Test canonical IDK check fails with non-exact match."""
    check = CanonicalIDKCheck()
    case = Case(id="test", input="q", expected_behavior="no_answer")
    result = check.check("I don't know.", case)
    assert not result.passed
