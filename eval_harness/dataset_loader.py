"""
Dataset loader for JSONL files.
"""
import json
from pathlib import Path
from typing import List
from .models import Case, Source


def load_dataset(dataset_path: str) -> List[Case]:
    """
    Load a JSONL dataset.

    Args:
        dataset_path: Path to JSONL file

    Returns:
        List of Case objects

    Raises:
        FileNotFoundError: If dataset file doesn't exist
        ValueError: If dataset format is invalid
    """
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    cases = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num}: {e}")

            # Validate required fields
            if 'id' not in data:
                raise ValueError(f"Line {line_num}: Missing required field 'id'")

            # Handle input/question alias
            if 'input' in data:
                input_text = data['input']
            elif 'question' in data:
                input_text = data['question']
            else:
                raise ValueError(f"Line {line_num}: Missing 'input' or 'question' field")

            # Parse sources if present
            sources = None
            if 'sources' in data:
                sources = [
                    Source(
                        doc_id=s['doc_id'],
                        page=s['page'],
                        locator=s.get('locator')
                    )
                    for s in data['sources']
                ]

            # Create case
            case = Case(
                id=data['id'],
                input=input_text,
                context=data.get('context'),
                sources=sources,
                expected_behavior=data.get('expected_behavior'),
                tags=data.get('tags'),
                reference_answer=data.get('reference_answer'),
                difficulty=data.get('difficulty'),
                extra={k: v for k, v in data.items() if k not in [
                    'id', 'input', 'question', 'context', 'sources',
                    'expected_behavior', 'tags', 'reference_answer', 'difficulty'
                ]}
            )

            cases.append(case)

    return cases
