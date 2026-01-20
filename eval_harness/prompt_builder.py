"""
Prompt builder for candidates.
"""
from typing import List, Dict, Any, Optional
from .models import Case, ContextChunk


def build_candidate_prompt(case: Case, context_chunks: List[ContextChunk] = None) -> str:
    """
    Build a prompt for a candidate model.

    Args:
        case: Case to build prompt for
        context_chunks: Optional context chunks (from oracle builder or case.context)

    Returns:
        Formatted prompt string
    """
    # Start with the question/input
    prompt_parts = []

    # Add context if present
    if context_chunks:
        # Context from oracle builder (ContextChunk objects)
        # Oracle builder already handles page_offset internally
        context_text = "\n\n".join([
            f"[{chunk.doc_id} p{chunk.dataset_page}]\n{chunk.text}"
            for chunk in context_chunks
        ])
        prompt_parts.append(f"Context:\n{context_text}")
    elif case.context:
        # Context from dataset (dict format)
        context_text = "\n\n".join([
            _format_embedded_context_chunk(ctx)
            for ctx in case.context
        ])
        prompt_parts.append(f"Context:\n{context_text}")

    # Add the question
    prompt_parts.append(f"Question: {case.input}")

    return "\n\n".join(prompt_parts)


def _format_embedded_context_chunk(ctx: Dict[str, Any]) -> str:
    """
    Format a single embedded context chunk.

    Args:
        ctx: Context dictionary with doc_id, page, text

    Returns:
        Formatted context chunk string
    """
    # If no doc_id, just return text
    if 'doc_id' not in ctx:
        return ctx.get('text', '')

    # Get page number directly (no offset)
    page = ctx.get('page', 0)

    doc_id = ctx.get('doc_id', 'UNKNOWN')
    text = ctx.get('text', '')

    return f"[{doc_id} p{page}]\n{text}"
