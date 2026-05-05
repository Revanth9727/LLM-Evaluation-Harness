"""
Artifact writer - writes all run outputs.
"""
import json
import yaml
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from ..models import Case, CandidateOutput, HardCheckResult, JudgeVote
from ..metrics import (
    calculate_win_rate,
    calculate_refusal_rate,
    calculate_format_pass_rate,
    bootstrap_ci,
    get_win_rate_samples
)


class ArtifactWriter:
    """Writes artifacts for a run."""

    def __init__(self, config: Dict[str, Any], run_dir: Path):
        """
        Initialize artifact writer.

        Args:
            config: Run configuration
            run_dir: Directory to write artifacts to
        """
        self.config = config
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def write_all(
        self,
        cases: List[Case],
        outputs: Dict[str, Dict[str, CandidateOutput]],  # {case_id: {"A": output, "B": output}}
        hard_checks: Dict[str, Dict[str, List[HardCheckResult]]],  # {case_id: {"A": results, "B": results}}
        judge_votes: List[JudgeVote],
        run_meta: Dict[str, Any]
    ):
        """
        Write all artifacts.

        Args:
            cases: List of cases
            outputs: Candidate outputs by case
            hard_checks: Hard check results by case
            judge_votes: Judge votes
            run_meta: Run metadata
        """
        # Write config snapshot
        self._write_config()

        # Write run metadata
        self._write_run_meta(run_meta)

        # Write cases
        self._write_cases(cases)

        # Write outputs
        self._write_outputs(outputs)

        # Write hard checks
        self._write_hard_checks(hard_checks)

        # Write judge votes
        if judge_votes:
            self._write_judge_votes(judge_votes)

        # Write summary
        self._write_summary(cases, outputs, hard_checks, judge_votes)

    def _write_config(self):
        """Write config snapshot."""
        config_path = self.run_dir / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def _write_run_meta(self, run_meta: Dict[str, Any]):
        """Write run metadata."""
        meta_path = self.run_dir / "run_meta.json"
        with open(meta_path, 'w') as f:
            json.dump(run_meta, f, indent=2)

    def _write_cases(self, cases: List[Case]):
        """Write cases.jsonl."""
        cases_path = self.run_dir / "cases.jsonl"
        with open(cases_path, 'w', encoding='utf-8') as f:
            for case in cases:
                case_dict = {
                    'id': case.id,
                    'input': case.input,
                    'expected_behavior': case.expected_behavior,
                    'tags': case.tags
                }
                if case.context:
                    case_dict['context'] = case.context
                if case.sources:
                    case_dict['sources'] = [
                        {'doc_id': s.doc_id, 'page': s.page, 'locator': s.locator}
                        for s in case.sources
                    ]
                f.write(json.dumps(case_dict) + '\n')

    def _write_outputs(self, outputs: Dict[str, Dict[str, CandidateOutput]]):
        """Write outputs.jsonl."""
        outputs_path = self.run_dir / "outputs.jsonl"
        with open(outputs_path, 'w', encoding='utf-8') as f:
            for case_id, case_outputs in outputs.items():
                output_dict = {'case_id': case_id}
                for candidate, output in case_outputs.items():
                    output_dict[f'output_{candidate.lower()}'] = output.output
                    if output.error:
                        output_dict[f'error_{candidate.lower()}'] = output.error
                    if output.latency_ms:
                        output_dict[f'latency_ms_{candidate.lower()}'] = output.latency_ms
                f.write(json.dumps(output_dict) + '\n')

    def _write_hard_checks(self, hard_checks: Dict[str, Dict[str, List[HardCheckResult]]]):
        """
        Write hard_checks.jsonl.
        One line per case+candidate combination.
        """
        hard_checks_path = self.run_dir / "hard_checks.jsonl"
        with open(hard_checks_path, 'w', encoding='utf-8') as f:
            for case_id, case_checks in hard_checks.items():
                for candidate, results in case_checks.items():
                    check_dict = {
                        'case_id': case_id,
                        'candidate': candidate,
                        'checks': [
                            {
                                'name': r.name,
                                'passed': r.passed,
                                'severity': r.severity,
                                'reason': r.reason,
                                'details': r.details
                            }
                            for r in results
                        ],
                        'all_passed': all(r.passed for r in results if r.severity == 'error')
                    }
                    f.write(json.dumps(check_dict) + '\n')

    def _write_judge_votes(self, judge_votes: List[JudgeVote]):
        """Write judge_votes.jsonl."""
        votes_path = self.run_dir / "judge_votes.jsonl"
        with open(votes_path, 'w', encoding='utf-8') as f:
            for vote in judge_votes:
                vote_dict = {
                    'case_id': vote.case_id,
                    'winner': vote.winner,
                    'confidence': vote.confidence,
                    'reasons': vote.reasons,
                    'citations_assessed': vote.citations_assessed,
                    'notes': vote.notes
                }
                f.write(json.dumps(vote_dict) + '\n')

    def _write_summary(
        self,
        cases: List[Case],
        outputs: Dict[str, Dict[str, CandidateOutput]],
        hard_checks: Dict[str, Dict[str, List[HardCheckResult]]],
        judge_votes: List[JudgeVote]
    ):
        """Write summary.json and summary.md."""
        # Calculate stats
        total_cases = len(cases)

        # Hard check stats
        a_hard_check_failures = sum(
            1 for case_id, checks in hard_checks.items()
            if not all(r.passed for r in checks.get('A', []) if r.severity == 'error')
        )
        b_hard_check_failures = sum(
            1 for case_id, checks in hard_checks.items()
            if not all(r.passed for r in checks.get('B', []) if r.severity == 'error')
        )

        # Judge stats
        judge_stats = {}
        if judge_votes:
            judge_stats = {
                'total_judged': len(judge_votes),
                'a_wins': sum(1 for v in judge_votes if v.winner == 'A'),
                'b_wins': sum(1 for v in judge_votes if v.winner == 'B'),
                'ties': sum(1 for v in judge_votes if v.winner == 'tie'),
                'uncertain': sum(1 for v in judge_votes if v.winner == 'uncertain'),
                'avg_confidence': sum(v.confidence for v in judge_votes) / len(judge_votes) if judge_votes else 0
            }

        # J1) Calculate new metrics
        canonical_idk = self.config.get('task_contract', {}).get('canonical_idk')

        win_rate = calculate_win_rate([v.__dict__ if hasattr(v, '__dict__') else v for v in judge_votes])
        refusal_rates = calculate_refusal_rate(outputs, canonical_idk)
        format_pass_rates = calculate_format_pass_rate(hard_checks)

        # J2) Bootstrap CI for win_rate
        win_rate_ci = None
        if win_rate is not None:
            samples = get_win_rate_samples([v.__dict__ if hasattr(v, '__dict__') else v for v in judge_votes])
            if samples:
                bootstrap_samples = self.config.get('gates', {}).get('bootstrap_samples', 1000)
                confidence_level = self.config.get('gates', {}).get('confidence_level', 0.95)
                ci_lower, ci_upper = bootstrap_ci(samples, n_resamples=bootstrap_samples, ci_level=confidence_level)
                win_rate_ci = {'lower': ci_lower, 'upper': ci_upper}

        # Per-tag breakdown
        tags_breakdown = self._calculate_tag_breakdown(cases, hard_checks, judge_votes)

        # Top failures
        top_failures = self._find_top_failures(cases, outputs, hard_checks, judge_votes)

        # Budget stats
        budget_stats = self._calculate_budget_stats(outputs, hard_checks)

        # Build summary
        summary = {
            'run_name': self.config.get('run_name', 'unknown'),
            'total_cases': total_cases,
            'hard_checks': {
                'candidate_a_failures': a_hard_check_failures,
                'candidate_b_failures': b_hard_check_failures
            },
            'judge': judge_stats,
            'metrics': {
                'win_rate': win_rate,
                'win_rate_ci': win_rate_ci,
                'refusal_rate_a': refusal_rates['candidate_a'],
                'refusal_rate_b': refusal_rates['candidate_b'],
                'format_pass_rate_a': format_pass_rates['candidate_a'],
                'format_pass_rate_b': format_pass_rates['candidate_b']
            },
            'per_tag_breakdown': tags_breakdown,
            'budget_stats': budget_stats
        }

        # Write JSON
        summary_json_path = self.run_dir / "summary.json"
        with open(summary_json_path, 'w') as f:
            json.dump(summary, f, indent=2)

        # Write Markdown
        self._write_summary_md(summary, top_failures)

    def _calculate_tag_breakdown(
        self,
        cases: List[Case],
        hard_checks: Dict[str, Dict[str, List[HardCheckResult]]],
        judge_votes: List[JudgeVote]
    ) -> Dict[str, Any]:
        """Calculate per-tag breakdown."""
        # Group cases by tag
        tags_map = {}
        for case in cases:
            for tag in (case.tags or []):
                if tag not in tags_map:
                    tags_map[tag] = []
                tags_map[tag].append(case.id)

        # Calculate stats per tag
        breakdown = {}
        for tag, case_ids in tags_map.items():
            tag_votes = [v for v in judge_votes if (v.case_id if hasattr(v, 'case_id') else v.get('case_id')) in case_ids]
            tag_hard_checks = {cid: checks for cid, checks in hard_checks.items() if cid in case_ids}

            a_fails = sum(
                1 for cid, checks in tag_hard_checks.items()
                if not all(r.passed for r in checks.get('A', []) if r.severity == 'error')
            )
            b_fails = sum(
                1 for cid, checks in tag_hard_checks.items()
                if not all(r.passed for r in checks.get('B', []) if r.severity == 'error')
            )

            breakdown[tag] = {
                'total_cases': len(case_ids),
                'a_hard_check_failures': a_fails,
                'b_hard_check_failures': b_fails,
                'total_judged': len(tag_votes)
            }

        return breakdown

    def _find_top_failures(
        self,
        cases: List[Case],
        outputs: Dict[str, Dict[str, CandidateOutput]],
        hard_checks: Dict[str, Dict[str, List[HardCheckResult]]],
        judge_votes: List[JudgeVote]
    ) -> List[Dict[str, Any]]:
        """Find top 3 failure examples."""
        failures = []

        for case in cases:
            case_id = case.id

            # Check for hard check failures
            a_checks = hard_checks.get(case_id, {}).get('A', [])
            b_checks = hard_checks.get(case_id, {}).get('B', [])

            a_failed = not all(r.passed for r in a_checks if r.severity == 'error')
            b_failed = not all(r.passed for r in b_checks if r.severity == 'error')

            if a_failed or b_failed:
                failure_info = {
                    'case_id': case_id,
                    'reason': 'hard_check_failure',
                    'details': []
                }

                if a_failed:
                    failed_checks = [r.name for r in a_checks if not r.passed and r.severity == 'error']
                    failure_info['details'].append(f"A failed: {', '.join(failed_checks)}")

                if b_failed:
                    failed_checks = [r.name for r in b_checks if not r.passed and r.severity == 'error']
                    failure_info['details'].append(f"B failed: {', '.join(failed_checks)}")

                failures.append(failure_info)

        # Return top 3
        return failures[:3]

    def _calculate_budget_stats(
        self,
        outputs: Dict[str, Dict[str, CandidateOutput]],
        hard_checks: Dict[str, Dict[str, List[HardCheckResult]]]
    ) -> Dict[str, Any]:
        """Calculate budget statistics."""
        latencies_a = []
        latencies_b = []
        tokens_a = []
        tokens_b = []

        for case_id, case_outputs in outputs.items():
            # Latency
            a_out = case_outputs.get('A')
            b_out = case_outputs.get('B')

            if a_out and a_out.latency_ms:
                latencies_a.append(a_out.latency_ms)
            if b_out and b_out.latency_ms:
                latencies_b.append(b_out.latency_ms)

            # Token estimation from hard checks (if cost_proxy check exists)
            a_checks = hard_checks.get(case_id, {}).get('A', [])
            b_checks = hard_checks.get(case_id, {}).get('B', [])

            for check in a_checks:
                if check.name == 'cost_proxy' and check.details:
                    tokens_a.append(check.details.get('estimated_tokens', 0))

            for check in b_checks:
                if check.name == 'cost_proxy' and check.details:
                    tokens_b.append(check.details.get('estimated_tokens', 0))

        return {
            'latency_ms': {
                'candidate_a': {
                    'avg': sum(latencies_a) / len(latencies_a) if latencies_a else None,
                    'max': max(latencies_a) if latencies_a else None
                },
                'candidate_b': {
                    'avg': sum(latencies_b) / len(latencies_b) if latencies_b else None,
                    'max': max(latencies_b) if latencies_b else None
                }
            },
            'estimated_tokens': {
                'candidate_a': {
                    'total': sum(tokens_a) if tokens_a else None
                },
                'candidate_b': {
                    'total': sum(tokens_b) if tokens_b else None
                }
            }
        }

    def _write_summary_md(self, summary: Dict[str, Any], top_failures: List[Dict[str, Any]]):
        """Write summary.md with enhanced sections."""
        summary_md_path = self.run_dir / "summary.md"
        with open(summary_md_path, 'w') as f:
            f.write(f"# Evaluation Summary: {summary['run_name']}\n\n")
            f.write(f"**Total Cases:** {summary['total_cases']}\n\n")

            # Metrics (J1 + J2)
            f.write("## Metrics\n\n")
            metrics = summary['metrics']

            if metrics['win_rate'] is not None:
                f.write(f"- **Win Rate (A):** {metrics['win_rate']:.3f}\n")
                if metrics['win_rate_ci']:
                    ci = metrics['win_rate_ci']
                    f.write(f"  - **95% CI:** [{ci['lower']:.3f}, {ci['upper']:.3f}]\n")
            else:
                f.write("- **Win Rate (A):** N/A (no valid judge votes)\n")

            f.write(f"- **Refusal Rate (A):** {metrics['refusal_rate_a']:.3f}\n")
            f.write(f"- **Refusal Rate (B):** {metrics['refusal_rate_b']:.3f}\n")
            f.write(f"- **Format Pass Rate (A):** {metrics['format_pass_rate_a']:.3f}\n")
            f.write(f"- **Format Pass Rate (B):** {metrics['format_pass_rate_b']:.3f}\n\n")

            # Hard checks
            f.write("## Hard Check Results\n\n")
            f.write(f"- **Candidate A Failures:** {summary['hard_checks']['candidate_a_failures']}/{summary['total_cases']}\n")
            f.write(f"- **Candidate B Failures:** {summary['hard_checks']['candidate_b_failures']}/{summary['total_cases']}\n\n")

            # Judge
            if summary['judge']:
                f.write("## Judge Results\n\n")
                judge = summary['judge']
                f.write(f"- **Total Judged:** {judge['total_judged']}\n")
                f.write(f"- **A Wins:** {judge['a_wins']}\n")
                f.write(f"- **B Wins:** {judge['b_wins']}\n")
                f.write(f"- **Ties:** {judge['ties']}\n")
                f.write(f"- **Uncertain:** {judge['uncertain']}\n")
                f.write(f"- **Average Confidence:** {judge['avg_confidence']:.2f}\n\n")

            # Per-tag breakdown (C)
            if summary.get('per_tag_breakdown'):
                f.write("## Per-Tag Breakdown\n\n")
                for tag, stats in summary['per_tag_breakdown'].items():
                    f.write(f"### {tag}\n\n")
                    f.write(f"- **Total Cases:** {stats['total_cases']}\n")
                    f.write(f"- **A Hard Check Failures:** {stats['a_hard_check_failures']}\n")
                    f.write(f"- **B Hard Check Failures:** {stats['b_hard_check_failures']}\n")
                    f.write(f"- **Total Judged:** {stats['total_judged']}\n\n")

            # Top failures (C)
            if top_failures:
                f.write("## Top Failures\n\n")
                for i, failure in enumerate(top_failures, 1):
                    f.write(f"### {i}. Case: {failure['case_id']}\n\n")
                    f.write(f"- **Reason:** {failure['reason']}\n")
                    for detail in failure['details']:
                        f.write(f"- {detail}\n")
                    f.write("\n")

            # Budget stats (C)
            budget = summary.get('budget_stats', {})
            if budget:
                f.write("## Budget Statistics\n\n")

                latency = budget.get('latency_ms', {})
                if latency.get('candidate_a', {}).get('avg') is not None:
                    f.write("### Latency (ms)\n\n")
                    f.write(f"- **Candidate A:** avg={latency['candidate_a']['avg']:.1f}, max={latency['candidate_a']['max']:.1f}\n")
                    f.write(f"- **Candidate B:** avg={latency['candidate_b']['avg']:.1f}, max={latency['candidate_b']['max']:.1f}\n\n")

                tokens = budget.get('estimated_tokens', {})
                if tokens.get('candidate_a', {}).get('total') is not None:
                    f.write("### Estimated Tokens\n\n")
                    f.write(f"- **Candidate A Total:** {tokens['candidate_a']['total']}\n")
                    f.write(f"- **Candidate B Total:** {tokens['candidate_b']['total']}\n\n")


def get_git_sha() -> str:
    """
    Get current git SHA.

    Returns:
        Short git SHA or 'unknown'
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return 'unknown'


def create_run_id(run_name: str) -> str:
    """
    Create a run ID.

    Args:
        run_name: Name of the run

    Returns:
        Run ID in format: <run_name>_<timestamp>_<git_sha>
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    git_sha = get_git_sha()

    if git_sha != 'unknown':
        return f"{run_name}_{timestamp}_{git_sha}"
    else:
        return f"{run_name}_{timestamp}"
