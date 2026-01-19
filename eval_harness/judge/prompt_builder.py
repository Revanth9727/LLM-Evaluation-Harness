"""
Judge prompt builder.
"""
import random
from pathlib import Path
from typing import Dict, Any
from ..models import Case


def load_rubric(rubric_path: str) -> str:
    """
    Load judge rubric from file.

    Args:
        rubric_path: Path to rubric file

    Returns:
        Rubric text
    """
    path = Path(rubric_path)
    if not path.exists():
        raise FileNotFoundError(f"Rubric not found: {rubric_path}")

    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def build_judge_prompt(
    case: Case,
    answer_a: str,
    answer_b: str,
    rubric: str,
    randomize_order: bool = True,
    seed: int = None
) -> tuple[str, bool]:
    """
    Build judge prompt.

    Args:
        case: Case being judged
        answer_a: Answer from candidate A
        answer_b: Answer from candidate B
        rubric: Judge rubric text
        randomize_order: Whether to randomize A/B order
        seed: Random seed for order randomization

    Returns:
        Tuple of (prompt, swapped) where swapped=True if order was swapped
    """
    # Randomize order if requested
    swapped = False
    if randomize_order and seed is not None:
        rng = random.Random(seed)
        swapped = rng.choice([True, False])

    if swapped:
        first_label, first_answer = "B", answer_b
        second_label, second_answer = "A", answer_a
    else:
        first_label, first_answer = "A", answer_a
        second_label, second_answer = "B", answer_b

    # Build prompt
    prompt = f"""{rubric}

---

QUESTION:
{case.input}

EXPECTED_BEHAVIOR:
{case.expected_behavior or 'answer_with_citations'}

TAGS:
{', '.join(case.tags) if case.tags else 'none'}

ANSWER_{first_label}:
{first_answer}

ANSWER_{second_label}:
{second_answer}

---

Please evaluate both answers and return your judgment in strict JSON format:
{{
  "winner": "A|B|tie|uncertain",
  "confidence": 0.0-1.0,
  "reasons": ["..."],
  "citations_assessed": ["..."],
  "notes": "..."
}}
"""

    return prompt, swapped
