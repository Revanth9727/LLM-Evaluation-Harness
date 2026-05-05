"""
Main evaluation runner.
"""
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from .config import load_config, validate_run_config
from .dataset_loader import load_dataset
from .prompt_builder import build_candidate_prompt
from .providers.factory import create_provider
from .hard_checks.runner import HardCheckRunner
from .judge.runner import JudgeRunner
from .artifacts.writer import ArtifactWriter, create_run_id
from .models import Case, CandidateOutput, HardCheckResult, JudgeVote, ContextChunk, ModelResponse
from .runtime.callables import load_callable_from_string, normalize_model_response
from .utils.seed import set_seed
from .utils.logging import setup_logging
from .utils.system_prompts import load_system_prompt
from .context_builder.oracle import OracleContextBuilder
import json


def evaluate_gates(config: Dict[str, Any], run_dir: Path, logger) -> int:
    """
    Evaluate gates and regression checks.

    Args:
        config: Run configuration
        run_dir: Artifact directory
        logger: Logger instance

    Returns:
        Exit code: 0 if PASS, 2 if FAIL
    """
    gates_config = config.get('gates', {})
    regression_config = config.get('regression', {})
    gates_enabled = gates_config.get('enabled', False)

    # Load summary
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        logger.warning("summary.json not found, cannot evaluate gates")
        return 0

    with open(summary_path, 'r') as f:
        summary = json.load(f)

    # If gates disabled, write disabled state and return
    if not gates_enabled:
        logger.info("Gates disabled, skipping gate evaluation")

        # Write gate result to summary
        gate_result = {
            'enabled': False,
            'decision': 'SKIPPED',
            'reasons': [],
            'thresholds': {}
        }
        summary['gate'] = gate_result

        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        # Append to summary.md
        summary_md_path = run_dir / "summary.md"
        with open(summary_md_path, 'a') as f:
            f.write("## Gate Decision: SKIPPED\n\n")
            f.write("Gates are disabled in configuration.\n\n")

        return 0

    metrics = summary.get('metrics', {})
    failures = []
    warnings = []
    thresholds_checked = {}

    # Fail closed when there are no decisive outcomes
    if metrics.get('win_rate') is None:
        failures.append("No decisive judge outcomes (all non-judgeable or uncertain)")

    # J3) Check thresholds
    logger.info("Evaluating gate thresholds...")

    # win_rate_min
    win_rate_min = gates_config.get('win_rate_min')
    if win_rate_min is not None:
        thresholds_checked['win_rate_min'] = win_rate_min
        win_rate = metrics.get('win_rate')
        if win_rate is None:
            warnings.append(f"win_rate_min threshold defined but win_rate is None (no valid votes)")
        elif win_rate < win_rate_min:
            failures.append(f"win_rate {win_rate:.3f} < threshold {win_rate_min}")
        else:
            logger.info(f"✓ win_rate {win_rate:.3f} >= {win_rate_min}")

    # win_rate_ci_lower_min
    win_rate_ci_lower_min = gates_config.get('win_rate_ci_lower_min')
    if win_rate_ci_lower_min is not None:
        thresholds_checked['win_rate_ci_lower_min'] = win_rate_ci_lower_min
        win_rate_ci = metrics.get('win_rate_ci')
        if win_rate_ci is None:
            warnings.append(f"win_rate_ci_lower_min threshold defined but CI not computed")
        else:
            ci_lower = win_rate_ci['lower']
            if ci_lower < win_rate_ci_lower_min:
                failures.append(f"win_rate CI lower bound {ci_lower:.3f} < threshold {win_rate_ci_lower_min}")
            else:
                logger.info(f"✓ win_rate CI lower {ci_lower:.3f} >= {win_rate_ci_lower_min}")

    # refusal_rate_max
    refusal_rate_max = gates_config.get('refusal_rate_max')
    if refusal_rate_max is not None:
        thresholds_checked['refusal_rate_max'] = refusal_rate_max
        refusal_a = metrics.get('refusal_rate_a', 0.0)
        refusal_b = metrics.get('refusal_rate_b', 0.0)
        if refusal_a > refusal_rate_max:
            failures.append(f"refusal_rate_a {refusal_a:.3f} > threshold {refusal_rate_max}")
        else:
            logger.info(f"✓ refusal_rate_a {refusal_a:.3f} <= {refusal_rate_max}")

        if refusal_b > refusal_rate_max:
            failures.append(f"refusal_rate_b {refusal_b:.3f} > threshold {refusal_rate_max}")
        else:
            logger.info(f"✓ refusal_rate_b {refusal_b:.3f} <= {refusal_rate_max}")

    # format_pass_rate_min
    format_pass_rate_min = gates_config.get('format_pass_rate_min')
    if format_pass_rate_min is not None:
        thresholds_checked['format_pass_rate_min'] = format_pass_rate_min
        format_a = metrics.get('format_pass_rate_a', 1.0)
        format_b = metrics.get('format_pass_rate_b', 1.0)
        if format_a < format_pass_rate_min:
            failures.append(f"format_pass_rate_a {format_a:.3f} < threshold {format_pass_rate_min}")
        else:
            logger.info(f"✓ format_pass_rate_a {format_a:.3f} >= {format_pass_rate_min}")

        if format_b < format_pass_rate_min:
            failures.append(f"format_pass_rate_b {format_b:.3f} < threshold {format_pass_rate_min}")
        else:
            logger.info(f"✓ format_pass_rate_b {format_b:.3f} >= {format_pass_rate_min}")

    # J4) Regression check
    if regression_config.get('enabled', False):
        logger.info("Evaluating regression check...")
        baseline_path = regression_config.get('baseline_summary_path')
        tolerance = regression_config.get('win_rate_drop_tolerance')

        if baseline_path and tolerance is not None:
            baseline_path = Path(baseline_path)
            if baseline_path.exists():
                with open(baseline_path, 'r') as f:
                    baseline_summary = json.load(f)

                baseline_win_rate = baseline_summary.get('metrics', {}).get('win_rate')
                current_win_rate = metrics.get('win_rate')

                if baseline_win_rate is not None and current_win_rate is not None:
                    drop = baseline_win_rate - current_win_rate
                    if drop > tolerance:
                        failures.append(f"win_rate dropped {drop:.3f} (baseline: {baseline_win_rate:.3f}, current: {current_win_rate:.3f}, tolerance: {tolerance})")
                    else:
                        logger.info(f"✓ win_rate drop {drop:.3f} <= tolerance {tolerance}")
                else:
                    warnings.append("Regression check: win_rate not available in baseline or current")
            else:
                warnings.append(f"Regression check: baseline_summary_path {baseline_path} not found")
        else:
            warnings.append("Regression check enabled but baseline_summary_path or tolerance not configured")

    # Warnings
    for warning in warnings:
        logger.warning(f"⚠ {warning}")

    # Gate decision
    if failures:
        gate_decision = "FAIL"
        exit_code = 2
        logger.error("=" * 60)
        logger.error("GATE DECISION: FAIL")
        logger.error("=" * 60)
        for failure in failures:
            logger.error(f"✗ {failure}")
        logger.error("=" * 60)
    else:
        gate_decision = "PASS"
        exit_code = 0
        logger.info("=" * 60)
        logger.info("GATE DECISION: PASS")
        logger.info("=" * 60)

    # Write gate result to summary
    summary['gate'] = {
        'enabled': True,
        'decision': gate_decision,
        'reasons': failures,
        'thresholds': thresholds_checked
    }

    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # Append to summary.md
    summary_md_path = run_dir / "summary.md"
    with open(summary_md_path, 'a') as f:
        f.write(f"## Gate Decision: {gate_decision}\n\n")

        # Show thresholds
        if thresholds_checked:
            f.write("**Thresholds Checked:**\n\n")
            for threshold_name, threshold_value in thresholds_checked.items():
                f.write(f"- `{threshold_name}`: {threshold_value}\n")
            f.write("\n")

        if failures:
            f.write("**Failures:**\n\n")
            for failure in failures:
                f.write(f"- ✗ {failure}\n")
            f.write("\n")

        if warnings:
            f.write("**Warnings:**\n\n")
            for warning in warnings:
                f.write(f"- ⚠ {warning}\n")
            f.write("\n")

    return exit_code


def _serialize_context_for_callable(
    case: Case,
    context_chunks: Optional[List[ContextChunk]]
) -> Optional[List[Dict[str, Any]]]:
    """Convert context to serializable payload for BYO callable candidates."""
    if context_chunks is not None:
        return [
            {
                'doc_id': chunk.doc_id,
                'dataset_page': chunk.dataset_page,
                'corpus_page': chunk.corpus_page,
                'text': chunk.text,
                'truncated': chunk.truncated,
                'blank_page': chunk.blank_page,
            }
            for chunk in context_chunks
        ]

    return case.context


def _build_candidate_runtime(candidate_config: Dict[str, Any]) -> Dict[str, Any]:
    """Build runtime object for provider-backed or callable-backed candidate."""
    cand_config = candidate_config.copy()
    system_prompt = load_system_prompt(cand_config.pop('system_prompt_path', None))

    if 'callable' in cand_config:
        fn = load_callable_from_string(cand_config.pop('callable'))
        return {
            'mode': 'callable',
            'callable': fn,
            'system_prompt': system_prompt,
        }

    provider = create_provider(
        cand_config.pop('provider'),
        cand_config.pop('model'),
        **cand_config,
    )
    return {
        'mode': 'provider',
        'provider': provider,
        'system_prompt': system_prompt,
    }


def _run_candidate(
    runtime: Dict[str, Any],
    case: Case,
    context_chunks: Optional[List[ContextChunk]],
) -> ModelResponse:
    """Run a candidate runtime and return canonical ModelResponse."""
    if runtime['mode'] == 'provider':
        prompt = build_candidate_prompt(case, context_chunks)
        raw = runtime['provider'].generate(prompt, system_message=runtime['system_prompt'])
        return normalize_model_response(raw)

    context_payload = _serialize_context_for_callable(case, context_chunks)
    raw = runtime['callable'](
        input=case.input,
        context=context_payload,
        metadata=case.extra,
    )
    return normalize_model_response(raw)


def run_evaluation(config_path: str):
    """
    Run an A/B evaluation.

    Args:
        config_path: Path to config file
    """
    # Setup logging
    logger = setup_logging()
    logger.info(f"Loading config from {config_path}")

    # Load and validate config
    config = load_config(config_path)
    validate_run_config(config)

    # Set seed
    seed = config.get('reproducibility', {}).get('seed', 1337)
    set_seed(seed)
    logger.info(f"Set random seed to {seed}")

    # Load dataset
    dataset_path = config['dataset_path']
    logger.info(f"Loading dataset from {dataset_path}")
    cases = load_dataset(dataset_path)
    logger.info(f"Loaded {len(cases)} cases")

    # Create candidate runtimes
    logger.info("Initializing candidates...")
    candidate_runtimes = {
        'A': _build_candidate_runtime(config['candidates']['A']),
        'B': _build_candidate_runtime(config['candidates']['B']),
    }

    # Initialize judge if enabled
    judge_runner = None
    if config.get('judge', {}).get('enabled', False):
        logger.info("Initializing judge...")
        judge_config = config['judge'].copy()
        judge_callable: Optional[Callable[..., Any]] = None
        judge_provider = None

        if 'callable' in judge_config:
            judge_callable = load_callable_from_string(judge_config.pop('callable'))
        else:
            judge_provider = create_provider(
                judge_config.pop('provider'),
                judge_config.pop('model'),
                **{
                    k: v for k, v in judge_config.items()
                    if k not in ['enabled', 'rubric_path', 'order_randomization_seed', 'two_pass_on_uncertain', 'system_prompt_path']
                }
            )

        judge_runner = JudgeRunner(
            config['judge'],
            provider=judge_provider,
            judge_callable=judge_callable,
        )

    # Initialize hard check runner
    hard_checks_config = config.get('hard_checks', {}).copy()
    hard_checks_config['task_contract'] = config.get('task_contract', {})
    hard_check_runner = HardCheckRunner(hard_checks_config)

    # Initialize oracle context builder if needed
    oracle_builder = None
    if config.get('context_builder', {}).get('mode') == 'oracle_from_corpus':
        logger.info("Initializing oracle context builder...")
        oracle_builder = OracleContextBuilder(config['context_builder'])

    # Create output directory
    run_name = config['run_name']
    run_id = create_run_id(run_name)
    artifacts_root = Path(config.get('artifacts', {}).get('root_dir', 'artifacts'))
    run_dir = artifacts_root / run_id
    logger.info(f"Artifacts will be written to {run_dir}")

    # Storage for results
    outputs: Dict[str, Dict[str, CandidateOutput]] = {}
    hard_checks: Dict[str, Dict[str, List[HardCheckResult]]] = {}
    judge_votes: List[JudgeVote] = []

    # Process each case
    logger.info("Processing cases...")
    for i, case in enumerate(cases, 1):
        logger.info(f"[{i}/{len(cases)}] Processing case {case.id}")

        # Build context if using oracle mode
        context_chunks: Optional[List[ContextChunk]] = None
        context_build_error = None

        if oracle_builder:
            try:
                logger.info("  Building context from corpus...")
                context_chunks = oracle_builder.build_context(case)
                logger.info(f"  Built {len(context_chunks)} context chunks")
            except Exception as e:
                logger.error(f"  Context build failed: {e}")
                context_build_error = str(e)

        # Generate outputs from both candidates
        outputs[case.id] = {}
        hard_checks[case.id] = {}

        for candidate in ['A', 'B']:
            logger.info(f"  Generating output from candidate {candidate}")

            try:
                # Generate (only if context didn't fail)
                if context_build_error:
                    raise ValueError(f"Context build failed: {context_build_error}")

                start_time = time.time()
                model_response = _run_candidate(candidate_runtimes[candidate], case, context_chunks)
                measured_latency_ms = (time.time() - start_time) * 1000
                latency_ms = model_response.latency_ms if model_response.latency_ms is not None else measured_latency_ms

                outputs[case.id][candidate] = CandidateOutput(
                    case_id=case.id,
                    candidate=candidate,
                    output=model_response.output,
                    latency_ms=latency_ms,
                    citations=model_response.citations,
                    token_usage=model_response.token_usage,
                    model_id=model_response.model_id,
                    metadata=model_response.metadata,
                )

            except Exception as e:
                logger.error(f"  Error generating output for candidate {candidate}: {e}")
                outputs[case.id][candidate] = CandidateOutput(
                    case_id=case.id,
                    candidate=candidate,
                    output="",
                    error=str(e)
                )

        # Run hard checks
        for candidate in ['A', 'B']:
            output = outputs[case.id][candidate].output
            latency_ms = outputs[case.id][candidate].latency_ms
            results = hard_check_runner.run_checks(output, case, latency_ms=latency_ms)
            hard_checks[case.id][candidate] = results

            if hard_check_runner.has_failures(results):
                logger.warning(f"  Candidate {candidate} failed hard checks")

        # Run judge if both candidates passed hard checks
        a_passed = not hard_check_runner.has_failures(hard_checks[case.id]['A'])
        b_passed = not hard_check_runner.has_failures(hard_checks[case.id]['B'])

        if judge_runner and a_passed and b_passed:
            logger.info("  Running judge...")
            vote = judge_runner.judge_case(
                case,
                outputs[case.id]['A'].output,
                outputs[case.id]['B'].output
            )
            if vote:
                judge_votes.append(vote)
                logger.info(f"  Judge verdict: {vote.winner} (confidence: {vote.confidence:.2f})")
        elif judge_runner:
            logger.info("  Skipping judge (hard check failures)")

    # Write artifacts
    logger.info("Writing artifacts...")
    run_meta = {
        'seed': seed,
        'timestamp': run_id.split('_', 1)[1] if '_' in run_id else run_id,
        'total_cases': len(cases)
    }

    writer = ArtifactWriter(config, run_dir)
    writer.write_all(cases, outputs, hard_checks, judge_votes, run_meta)

    logger.info(f"Evaluation complete! Artifacts written to {run_dir}")
    logger.info(f"Summary: {len(cases)} cases, {len(judge_votes)} judged")

    # Evaluate gates (J3 + J4)
    gate_result = evaluate_gates(config, run_dir, logger)

    return gate_result


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m eval_harness.run --config <config_path>")
        sys.exit(1)

    # Parse arguments
    if '--config' not in sys.argv:
        print("Error: --config argument required")
        sys.exit(1)

    config_idx = sys.argv.index('--config')
    if config_idx + 1 >= len(sys.argv):
        print("Error: --config requires a value")
        sys.exit(1)

    config_path = sys.argv[config_idx + 1]

    # Run evaluation
    try:
        exit_code = run_evaluation(config_path)
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
