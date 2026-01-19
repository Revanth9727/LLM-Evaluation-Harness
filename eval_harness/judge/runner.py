"""
Judge runner.
"""
import json
import random
from typing import Dict, Any, Optional
from ..models import Case, JudgeVote
from ..providers.base import BaseProvider
from ..utils.system_prompts import load_system_prompt
from .prompt_builder import load_rubric, build_judge_prompt


class JudgeRunner:
    """Runs judge evaluations."""

    def __init__(self, config: Dict[str, Any], provider: BaseProvider):
        """
        Initialize judge runner.

        Args:
            config: Judge configuration
            provider: Judge provider
        """
        self.config = config
        self.provider = provider
        self.enabled = config.get('enabled', True)

        if self.enabled and 'rubric_path' in config:
            self.rubric = load_rubric(config['rubric_path'])
        else:
            self.rubric = ""

        # Load system prompt if specified
        self.system_prompt = load_system_prompt(config.get('system_prompt_path'))

        self.order_randomization_seed = config.get('order_randomization_seed', 1337)
        self.two_pass_on_uncertain = config.get('two_pass_on_uncertain', False)
        self._case_counter = 0

    def judge_case(
        self,
        case: Case,
        output_a: str,
        output_b: str
    ) -> Optional[JudgeVote]:
        """
        Judge a single case.

        Args:
            case: Case to judge
            output_a: Output from candidate A
            output_b: Output from candidate B

        Returns:
            JudgeVote or None if judge disabled
        """
        if not self.enabled:
            return None

        # Generate seed for this case (deterministic based on case order)
        case_seed = self.order_randomization_seed + self._case_counter
        self._case_counter += 1

        # Build prompt
        prompt, swapped = build_judge_prompt(
            case=case,
            answer_a=output_a,
            answer_b=output_b,
            rubric=self.rubric,
            randomize_order=True,
            seed=case_seed
        )

        # Get judge response
        try:
            raw_response = self.provider.generate(prompt, system_message=self.system_prompt)
            vote = self._parse_judge_response(raw_response, case.id, swapped)

            # Two-pass judging for uncertain votes
            if self.two_pass_on_uncertain and vote.confidence < 0.5:
                # Swap order and judge again
                prompt2, swapped2 = build_judge_prompt(
                    case=case,
                    answer_a=output_a,
                    answer_b=output_b,
                    rubric=self.rubric,
                    randomize_order=True,
                    seed=case_seed + 1000  # Different seed for second pass
                )

                raw_response2 = self.provider.generate(prompt2, system_message=self.system_prompt)
                vote2 = self._parse_judge_response(raw_response2, case.id, swapped2)

                # If votes disagree, mark as uncertain
                if vote.winner != vote2.winner:
                    vote.winner = "uncertain"
                    vote.confidence = min(vote.confidence, vote2.confidence)
                    vote.notes += f" [Two-pass disagreement: {vote.winner} vs {vote2.winner}]"

            return vote

        except Exception as e:
            # Return uncertain vote on error
            return JudgeVote(
                case_id=case.id,
                winner="uncertain",
                confidence=0.0,
                reasons=[f"Judge error: {str(e)}"],
                citations_assessed=[],
                notes="Error during judging",
                raw_response=""
            )

    def _parse_judge_response(
        self,
        raw_response: str,
        case_id: str,
        swapped: bool
    ) -> JudgeVote:
        """
        Parse judge JSON response.

        Args:
            raw_response: Raw response from judge
            case_id: Case ID
            swapped: Whether A/B order was swapped

        Returns:
            JudgeVote
        """
        try:
            # Extract JSON from response (may have markdown code blocks)
            response_text = raw_response.strip()
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()

            data = json.loads(response_text)

            # Un-swap winner if needed
            winner = data.get('winner', 'uncertain')
            if swapped and winner in ['A', 'B']:
                winner = 'B' if winner == 'A' else 'A'

            return JudgeVote(
                case_id=case_id,
                winner=winner,
                confidence=float(data.get('confidence', 0.0)),
                reasons=data.get('reasons', []),
                citations_assessed=data.get('citations_assessed', []),
                notes=data.get('notes', ''),
                raw_response=raw_response
            )

        except Exception as e:
            return JudgeVote(
                case_id=case_id,
                winner="uncertain",
                confidence=0.0,
                reasons=[f"Failed to parse judge response: {str(e)}"],
                citations_assessed=[],
                notes="Parse error",
                raw_response=raw_response
            )
