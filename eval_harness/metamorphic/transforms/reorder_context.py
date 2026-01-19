"""
Reorder context transform.
"""
import random
import copy
from .base import Transform
from ...models import Case


class ReorderContextTransform(Transform):
    """Reorder context chunks."""

    def transform(self, case: Case) -> Case:
        """
        Reorder context chunks.

        Args:
            case: Original case

        Returns:
            Case with reordered context
        """
        transformed = copy.deepcopy(case)
        transformed.id = f"{case.id}_reordered"

        if transformed.context and len(transformed.context) > 1:
            # Shuffle context
            shuffled = list(transformed.context)
            random.shuffle(shuffled)
            transformed.context = shuffled

        return transformed
