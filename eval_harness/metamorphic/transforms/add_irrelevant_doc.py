"""
Add irrelevant document transform.
"""
from ...models import Case
from .base import Transform


class AddIrrelevantDocTransform(Transform):
    """
    Add an irrelevant document chunk that should not be cited.
    The model should ignore this chunk and only cite valid sources.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)

    def transform(self, case: Case) -> Case:
        """
        Transform case by adding an irrelevant context chunk.

        Args:
            case: Original case

        Returns:
            Transformed case with irrelevant chunk added
        """
        # Create irrelevant chunk with a doc_id NOT in the allowed sources
        irrelevant_chunk = {
            'doc_id': 'IRRELEVANT_DOC',
            'page': 999,
            'text': 'This is completely unrelated information about ice cream flavors. Chocolate is the most popular flavor worldwide. Vanilla comes second. Strawberry is third.'
        }

        # Add to context (if context exists)
        if case.context:
            new_context = case.context + [irrelevant_chunk]
        else:
            new_context = [irrelevant_chunk]

        # Create new case with irrelevant chunk added
        transformed_case = Case(
            id=f"{case.id}_irrelevant",
            input=case.input,
            context=new_context,
            sources=case.sources,  # Don't add irrelevant doc to sources
            expected_behavior=case.expected_behavior,
            tags=case.tags
        )

        return transformed_case
