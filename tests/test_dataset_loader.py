"""
Tests for dataset loader.
"""
import pytest
import json
import tempfile
from pathlib import Path
from eval_harness.dataset_loader import load_dataset


def test_load_dataset_with_input():
    """Test loading dataset with 'input' field."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(json.dumps({"id": "test1", "input": "What is AI?"}) + '\n')
        temp_path = f.name

    try:
        cases = load_dataset(temp_path)
        assert len(cases) == 1
        assert cases[0].id == "test1"
        assert cases[0].input == "What is AI?"
    finally:
        Path(temp_path).unlink()


def test_load_dataset_with_question_alias():
    """Test loading dataset with 'question' as alias of 'input'."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write(json.dumps({"id": "test1", "question": "What is AI?"}) + '\n')
        temp_path = f.name

    try:
        cases = load_dataset(temp_path)
        assert len(cases) == 1
        assert cases[0].input == "What is AI?"
    finally:
        Path(temp_path).unlink()


def test_load_dataset_with_sources():
    """Test loading dataset with sources."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        data = {
            "id": "test1",
            "question": "What?",
            "sources": [{"doc_id": "DOC", "page": 5}]
        }
        f.write(json.dumps(data) + '\n')
        temp_path = f.name

    try:
        cases = load_dataset(temp_path)
        assert len(cases) == 1
        assert cases[0].sources is not None
        assert len(cases[0].sources) == 1
        assert cases[0].sources[0].doc_id == "DOC"
        assert cases[0].sources[0].page == 5
    finally:
        Path(temp_path).unlink()
