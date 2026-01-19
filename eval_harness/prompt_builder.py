"""
Prompt builder for candidates.
"""
from typing import List, Dict, Any
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
        context_text = "\n\n".join([
            f"[{chunk.doc_id} p{chunk.dataset_page}]\n{chunk.text}"
            for chunk in context_chunks
        ])
        prompt_parts.append(f"Context:\n{context_text}")
    elif case.context:
        # Context from dataset (dict format)
        context_text = "\n\n".join([
            f"[{ctx.get('doc_id', 'UNKNOWN')} p{ctx.get('page', 0)}]\n{ctx.get('text', '')}"
            if 'doc_id' in ctx
            else ctx.get('text', '')
            for ctx in case.context
        ])
        prompt_parts.append(f"Context:\n{context_text}")

    # Add the question
    prompt_parts.append(f"Question: {case.input}")

    return "\n\n".join(prompt_parts)
