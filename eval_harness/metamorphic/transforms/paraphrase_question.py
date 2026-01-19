"""
Paraphrase question transform (deterministic mock version).
"""
from ...models import Case
from .base import Transform


class ParaphraseQuestionTransform(Transform):
    """
    Paraphrase question using simple deterministic rules.
    This is a mock implementation that adds synonyms without LLM calls.
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        # Simple synonym mappings for deterministic paraphrasing
        self.synonyms = {
            'what': 'what',
            'how': 'in what way',
            'why': 'for what reason',
            'when': 'at what time',
            'where': 'in what location',
            'who': 'which person',
            'is': 'is',
            'are': 'are',
            'can': 'is it possible to',
            'does': 'does'
        }

    def transform(self, case: Case) -> Case:
        """
        Transform case by paraphrasing the question.

        Args:
            case: Original case

        Returns:
            Transformed case with paraphrased question
        """
        # Simple deterministic paraphrase: add "Can you explain:" prefix
        # This keeps the transform deterministic without needing an LLM
        paraphrased_input = f"Can you explain: {case.input}"

        # Create new case with paraphrased input
        transformed_case = Case(
            id=f"{case.id}_paraphrased",
            input=paraphrased_input,
            context=case.context,
            sources=case.sources,
            expected_behavior=case.expected_behavior,
            tags=case.tags
        )

        return transformed_case
