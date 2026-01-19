"""
Remove key chunk transform.
"""
import copy
from .base import Transform
from ...models import Case


class RemoveKeyChunkTransform(Transform):
    """Remove the first context chunk (tests IDK behavior)."""

    def transform(self, case: Case) -> Case:
        """
        Remove first context chunk.

        Args:
            case: Original case

        Returns:
            Case with first chunk removed
        """
        transformed = copy.deepcopy(case)
        transformed.id = f"{case.id}_remove_key"

        if transformed.context and len(transformed.context) > 0:
            # Remove first chunk
            transformed.context = transformed.context[1:]

        # Update expected behavior to require IDK
        transformed.expected_behavior = "no_answer"
        if not transformed.tags:
            transformed.tags = []
        if "should_say_idk" not in transformed.tags:
            transformed.tags.append("should_say_idk")

        return transformed
