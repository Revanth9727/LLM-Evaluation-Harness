"""
Tests for context builder.
"""
import pytest
import tempfile
from pathlib import Path
from eval_harness.models import Case, Source
from eval_harness.context_builder.oracle import OracleContextBuilder
from eval_harness.context_builder.chunker import truncate_text


def test_truncate_text():
    """Test text truncation."""
    text = "a" * 100
    truncated, was_truncated = truncate_text(text, 50)

    assert was_truncated
    assert len(truncated) <= 64  # 50 + "...[TRUNCATED]"
    assert truncated.endswith("...[TRUNCATED]")


def test_truncate_text_no_truncation():
    """Test text truncation when not needed."""
    text = "short text"
    truncated, was_truncated = truncate_text(text, 100)

    assert not was_truncated
    assert truncated == text


def test_oracle_context_builder():
    """Test oracle context builder."""
    # Create temp corpus
    with tempfile.TemporaryDirectory() as tmpdir:
        corpus_root = Path(tmpdir)
        doc_dir = corpus_root / "TEST_DOC"
        doc_dir.mkdir()

        # Create corpus file (page 25 = dataset page 4 + offset 21)
        corpus_file = doc_dir / "25.txt"
        corpus_file.write_text("This is page 4 content.")

        # Create case with sources
        case = Case(
            id="test",
            input="question",
            sources=[Source(doc_id="TEST_DOC", page=4)]
        )

        # Build context
        builder = OracleContextBuilder({
            'corpus_root': str(corpus_root),
            'page_offset': 21,
            'max_chars_per_chunk': 4000
        })

        chunks = builder.build_context(case)

        assert len(chunks) == 1
        assert chunks[0].doc_id == "TEST_DOC"
        assert chunks[0].dataset_page == 4  # Dataset page
        assert chunks[0].corpus_page == 25   # Corpus page
        assert chunks[0].text == "This is page 4 content."
        assert not chunks[0].truncated


def test_oracle_context_builder_blank_page():
    """Test oracle context builder with blank page."""
    with tempfile.TemporaryDirectory() as tmpdir:
        corpus_root = Path(tmpdir)
        doc_dir = corpus_root / "TEST_DOC"
        doc_dir.mkdir()

        # Create blank page
        corpus_file = doc_dir / "25.txt"
        corpus_file.write_text("[[BLANK_PAGE]]")

        case = Case(
            id="test",
            input="question",
            sources=[Source(doc_id="TEST_DOC", page=4)]
        )

        builder = OracleContextBuilder({
            'corpus_root': str(corpus_root),
            'page_offset': 21,
            'max_chars_per_chunk': 4000
        })

        chunks = builder.build_context(case)

        assert len(chunks) == 1
        assert chunks[0].blank_page
        assert chunks[0].text.strip() == "[[BLANK_PAGE]]"
