"""
Oracle context builder - builds context from corpus using sources[].
"""
from pathlib import Path
from typing import List, Dict, Any
from ..models import Case, ContextChunk, Source
from .chunker import truncate_text


class OracleContextBuilder:
    """Builds context from corpus files using gold sources."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize oracle context builder.

        Args:
            config: Context builder configuration
        """
        self.corpus_root = Path(config.get('corpus_root', 'corpus'))
        self.max_chars_per_chunk = config.get('max_chars_per_chunk', 4000)

    def build_context(self, case: Case) -> List[ContextChunk]:
        """
        Build context chunks from case sources.

        Args:
            case: Case with sources[] defined

        Returns:
            List of ContextChunk objects

        Raises:
            ValueError: If sources are missing or corpus files not found
        """
        if not case.sources:
            raise ValueError(f"Case {case.id} has no sources defined")

        chunks = []

        for source in case.sources:
            # Use dataset page directly (no offset)
            dataset_page = source.page

            # Build corpus file path using dataset page
            corpus_file = self.corpus_root / source.doc_id / f"{dataset_page}.txt"

            # Check if file exists
            if not corpus_file.exists():
                raise ValueError(
                    f"Corpus file not found for case {case.id}: {corpus_file}\n"
                    f"(dataset_page={dataset_page})"
                )

            # Read text
            with open(corpus_file, 'r', encoding='utf-8') as f:
                text = f.read()

            # Check for blank page
            is_blank = text.strip() == "[[BLANK_PAGE]]"

            # Truncate if needed (unless blank page)
            truncated = False
            if not is_blank:
                text, truncated = truncate_text(text, self.max_chars_per_chunk)

            # Create chunk
            chunk = ContextChunk(
                doc_id=source.doc_id,
                dataset_page=dataset_page,
                corpus_page=dataset_page,  # Same as dataset_page (no offset)
                text=text,
                truncated=truncated,
                blank_page=is_blank
            )

            chunks.append(chunk)

        return chunks
