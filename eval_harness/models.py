"""
Data models for the eval harness.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Source:
    """Represents a source document reference."""
    doc_id: str
    page: int
    locator: Optional[str] = None


@dataclass
class ContextChunk:
    """Represents a context chunk with header."""
    doc_id: str
    dataset_page: int
    corpus_page: Optional[int]
    text: str
    truncated: bool = False
    blank_page: bool = False


@dataclass
class Case:
    """Represents a single evaluation case."""
    id: str
    input: str
    context: Optional[List[Dict[str, Any]]] = None
    sources: Optional[List[Source]] = None
    expected_behavior: Optional[str] = None
    tags: Optional[List[str]] = None
    reference_answer: Optional[str] = None
    difficulty: Optional[str] = None

    # Additional fields from dataset
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CandidateOutput:
    """Represents output from a candidate model."""
    case_id: str
    candidate: str  # "A" or "B"
    output: str
    error: Optional[str] = None
    latency_ms: Optional[float] = None


@dataclass
class HardCheckResult:
    """Result from a hard check."""
    name: str
    passed: bool
    severity: str  # "error" or "warning"
    reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JudgeVote:
    """Result from judge evaluation."""
    case_id: str
    winner: str  # "A", "B", "tie", "uncertain"
    confidence: float
    reasons: List[str] = field(default_factory=list)
    citations_assessed: List[str] = field(default_factory=list)
    notes: str = ""
    raw_response: str = ""
