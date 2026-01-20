"""
Test prompt builder for embedded context (no page offset).
"""
import pytest
from eval_harness.prompt_builder import build_candidate_prompt, _format_embedded_context_chunk
from eval_harness.models import Case


def test_format_embedded_context_direct_page():
    """Test that page numbers are used directly (no offset)."""
    ctx = {'doc_id': 'HOLLM', 'page': 37, 'text': 'Test content.'}
    result = _format_embedded_context_chunk(ctx)

    assert '[HOLLM p37]' in result  # Page 37 stays p37
    assert 'Test content.' in result


def test_format_embedded_context_another_page():
    """Test another page number stays as-is."""
    ctx = {'doc_id': 'HOLLM', 'page': 42, 'text': 'Test content.'}
    result = _format_embedded_context_chunk(ctx)

    assert '[HOLLM p42]' in result  # Page 42 stays p42
    assert 'Test content.' in result


def test_format_embedded_context_missing_page():
    """Test that missing page defaults to 0."""
    ctx = {'doc_id': 'HOLLM', 'text': 'Test content.'}
    result = _format_embedded_context_chunk(ctx)

    # Should default to 0
    assert '[HOLLM p0]' in result
    assert 'Test content.' in result


def test_format_embedded_context_page_zero():
    """Test that page 0 is handled correctly."""
    ctx = {'doc_id': 'HOLLM', 'page': 0, 'text': 'Test content.'}
    result = _format_embedded_context_chunk(ctx)

    assert '[HOLLM p0]' in result
    assert 'Test content.' in result


def test_format_embedded_context_no_doc_id():
    """Test that missing doc_id returns just text."""
    ctx = {'page': 37, 'text': 'Test content.'}
    result = _format_embedded_context_chunk(ctx)

    # Should just return text without formatting
    assert result == 'Test content.'
    assert '[' not in result


def test_build_candidate_prompt_with_embedded_context():
    """Test full prompt building with embedded context (no offset)."""
    from eval_harness.models import Source

    case = Case(
        id='test_001',
        input='What is a transformer?',
        tags=['answer_with_citations'],
        sources=[Source(doc_id='HOLLM', page=15)],
        context=[
            {'doc_id': 'HOLLM', 'page': 37, 'text': 'Transformers use attention.'},
            {'doc_id': 'HOLLM', 'page': 38, 'text': 'Self-attention is key.'}
        ]
    )

    prompt = build_candidate_prompt(case)

    # Pages stay as-is (no offset)
    assert '[HOLLM p37]' in prompt
    assert '[HOLLM p38]' in prompt
    assert 'Transformers use attention.' in prompt
    assert 'Self-attention is key.' in prompt
    assert 'What is a transformer?' in prompt


def test_build_candidate_prompt_with_oracle_context():
    """Test that oracle context chunks use dataset_page directly."""
    from eval_harness.models import ContextChunk, Source

    case = Case(
        id='test_001',
        input='What is a transformer?',
        tags=['answer_with_citations'],
        sources=[Source(doc_id='HOLLM', page=15)],
        context=None
    )

    # Oracle builder returns ContextChunk objects with dataset_page
    context_chunks = [
        ContextChunk(doc_id='HOLLM', dataset_page=15, corpus_page=15, text='Transformers use attention.')
    ]

    prompt = build_candidate_prompt(case, context_chunks=context_chunks)

    # Should use dataset_page from chunk
    assert '[HOLLM p15]' in prompt
    assert 'Transformers use attention.' in prompt


def test_build_candidate_prompt_no_context():
    """Test that cases without context work normally."""
    case = Case(
        id='test_001',
        input='What is a transformer?',
        tags=['answer_with_citations'],
        sources=[],
        context=None
    )

    prompt = build_candidate_prompt(case)

    # Should just have the question
    assert 'What is a transformer?' in prompt
    assert 'Context:' not in prompt


def test_page_37_stays_page_37():
    """Test that page 37 displays as p37 (no offset)."""
    ctx = {'doc_id': 'HOLLM', 'page': 37, 'text': 'Attention mechanism content.'}
    result = _format_embedded_context_chunk(ctx)

    # Page 37 stays p37 (no offset)
    assert '[HOLLM p37]' in result
    assert 'Attention mechanism content.' in result
