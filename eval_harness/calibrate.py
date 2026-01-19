"""
Judge calibration runner.
"""
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
from .config import load_config
from .providers.factory import create_provider
from .judge.runner import JudgeRunner
from .judge.prompt_builder import build_judge_prompt, load_rubric
from .models import Case
from .utils.logging import setup_logging
from .utils.system_prompts import load_system_prompt
from .artifacts.writer import create_run_id


def load_calibration_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """
    Load calibration dataset.

    Schema: {id, question, context, answer_a, answer_b, expected_winner, rationale}

    Args:
        dataset_path: Path to JSONL file

    Returns:
        List of calibration cases
    """
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Calibration dataset not found: {dataset_path}")

    cases = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            cases.append(data)

    return cases


def run_calibration(config_path: str):
    """
    Run judge calibration.

    Args:
        config_path: Path to calibration config file
    """
    logger = setup_logging()
    logger.info(f"Loading calibration config from {config_path}")

    # Load config
    config = load_config(config_path)

    # Load calibration dataset
    dataset_path = config['dataset_path']
    logger.info(f"Loading calibration dataset from {dataset_path}")
    cal_cases = load_calibration_dataset(dataset_path)
    logger.info(f"Loaded {len(cal_cases)} calibration cases")

    # Initialize judge provider
    logger.info("Initializing judge provider...")
    judge_config = config['judge'].copy()

    # Load system prompt
    system_prompt = load_system_prompt(judge_config.get('system_prompt_path'))

    judge_provider = create_provider(
        judge_config.pop('provider'),
        judge_config.pop('model'),
        **{k: v for k, v in judge_config.items() if k not in ['enabled', 'rubric_path', 'system_prompt_path', 'order_randomization_seed', 'two_pass_on_uncertain', 'order_randomization_trials']}
    )

    # Load rubric
    rubric = load_rubric(config['judge']['rubric_path'])

    # Get calibration parameters
    num_trials = config['judge'].get('order_randomization_trials', 3)
    logger.info(f"Running {num_trials} trials per case")

    # Run calibration trials
    results = []
    for i, cal_case in enumerate(cal_cases, 1):
        logger.info(f"[{i}/{len(cal_cases)}] Calibrating case {cal_case['id']}")

        case_trials = []

        for trial in range(num_trials):
            # Create a minimal Case object for judge
            case = Case(
                id=cal_case['id'],
                input=cal_case.get('question', ''),
                context=cal_case.get('context'),
                expected_behavior=cal_case.get('expected_behavior', 'answer_with_citations'),
                tags=cal_case.get('tags')
            )

            # Build judge prompt
            seed = 1000 * i + trial  # Unique seed per trial
            prompt, swapped = build_judge_prompt(
                case=case,
                answer_a=cal_case['answer_a'],
                answer_b=cal_case['answer_b'],
                rubric=rubric,
                randomize_order=True,
                seed=seed
            )

            # Get judge response
            try:
                raw_response = judge_provider.generate(prompt, system_message=system_prompt)

                # Parse response
                try:
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

                    case_trials.append({
                        'trial': trial,
                        'winner': winner,
                        'confidence': data.get('confidence', 0.0),
                        'swapped': swapped
                    })

                except Exception as e:
                    logger.warning(f"  Trial {trial}: Failed to parse judge response: {e}")
                    case_trials.append({
                        'trial': trial,
                        'winner': 'uncertain',
                        'confidence': 0.0,
                        'swapped': swapped
                    })

            except Exception as e:
                logger.error(f"  Trial {trial}: Judge error: {e}")
                case_trials.append({
                    'trial': trial,
                    'winner': 'uncertain',
                    'confidence': 0.0,
                    'swapped': swapped
                })

        results.append({
            'case_id': cal_case['id'],
            'expected_winner': cal_case['expected_winner'],
            'trials': case_trials
        })

    # Calculate metrics
    logger.info("Calculating calibration metrics...")
    metrics = calculate_metrics(results)

    # Check thresholds
    thresholds = config.get('thresholds', {})
    threshold_results = check_thresholds(metrics, thresholds)

    # Write artifacts
    run_id = create_run_id(config.get('run_name', 'judge_calibration'))
    artifacts_root = Path(config.get('artifacts', {}).get('root_dir', 'artifacts'))
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing calibration artifacts to {run_dir}")

    # Write reliability.json
    reliability_data = {
        'metrics': metrics,
        'thresholds': thresholds,
        'threshold_results': threshold_results,
        'num_cases': len(cal_cases),
        'num_trials_per_case': num_trials
    }

    with open(run_dir / 'reliability.json', 'w') as f:
        json.dump(reliability_data, f, indent=2)

    # Write reliability.md
    write_reliability_markdown(run_dir / 'reliability.md', reliability_data)

    # Print summary
    logger.info("=" * 60)
    logger.info("CALIBRATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Agreement: {metrics['agreement_pct']:.1f}%")
    logger.info(f"Flip Rate: {metrics['flip_rate_pct']:.1f}%")
    logger.info(f"Order Bias: {metrics['order_bias_pct']:.1f}%")
    logger.info("")

    all_passed = all(threshold_results.values())

    for check, passed in threshold_results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {check}")

    logger.info("=" * 60)

    if all_passed:
        logger.info("All thresholds passed!")
        sys.exit(0)
    else:
        logger.error("Some thresholds failed!")
        sys.exit(1)


def calculate_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate calibration metrics.

    Args:
        results: List of case results with trials

    Returns:
        Dictionary of metrics
    """
    # Agreement: cases where judge matched expected winner
    agreements = []
    for result in results:
        expected = result['expected_winner']
        # Use majority vote across trials
        votes = [t['winner'] for t in result['trials']]
        if votes:
            majority_vote = max(set(votes), key=votes.count)
            agreements.append(majority_vote == expected)

    agreement_pct = 100 * sum(agreements) / len(agreements) if agreements else 0

    # Flip rate: cases where judge changed vote across trials
    flips = []
    for result in results:
        votes = [t['winner'] for t in result['trials']]
        if len(votes) > 1:
            # Check if all votes are the same
            all_same = all(v == votes[0] for v in votes)
            flips.append(not all_same)

    flip_rate_pct = 100 * sum(flips) / len(flips) if flips else 0

    # Order bias: difference in A wins when A is first vs second
    a_first_votes = []
    a_second_votes = []

    for result in results:
        for trial in result['trials']:
            if trial['winner'] == 'A':
                if trial['swapped']:
                    a_second_votes.append(1)
                else:
                    a_first_votes.append(1)
            else:
                if trial['swapped']:
                    a_second_votes.append(0)
                else:
                    a_first_votes.append(0)

    a_first_rate = sum(a_first_votes) / len(a_first_votes) if a_first_votes else 0
    a_second_rate = sum(a_second_votes) / len(a_second_votes) if a_second_votes else 0
    order_bias_pct = abs(a_first_rate - a_second_rate) * 100

    return {
        'agreement_pct': agreement_pct,
        'flip_rate_pct': flip_rate_pct,
        'order_bias_pct': order_bias_pct
    }


def check_thresholds(metrics: Dict[str, float], thresholds: Dict[str, float]) -> Dict[str, bool]:
    """
    Check if metrics meet thresholds.

    Args:
        metrics: Calculated metrics
        thresholds: Threshold values

    Returns:
        Dictionary of pass/fail results
    """
    results = {}

    if 'min_agreement_pct' in thresholds:
        results['min_agreement_pct'] = metrics['agreement_pct'] >= thresholds['min_agreement_pct']

    if 'max_flip_rate_pct' in thresholds:
        results['max_flip_rate_pct'] = metrics['flip_rate_pct'] <= thresholds['max_flip_rate_pct']

    if 'max_order_bias_pct' in thresholds:
        results['max_order_bias_pct'] = metrics['order_bias_pct'] <= thresholds['max_order_bias_pct']

    return results


def write_reliability_markdown(path: Path, data: Dict[str, Any]):
    """
    Write reliability markdown report.

    Args:
        path: Path to write markdown file
        data: Reliability data
    """
    with open(path, 'w') as f:
        f.write("# Judge Calibration Report\n\n")

        f.write("## Metrics\n\n")
        f.write(f"- **Agreement:** {data['metrics']['agreement_pct']:.1f}%\n")
        f.write(f"- **Flip Rate:** {data['metrics']['flip_rate_pct']:.1f}%\n")
        f.write(f"- **Order Bias:** {data['metrics']['order_bias_pct']:.1f}%\n\n")

        f.write("## Thresholds\n\n")
        for check, passed in data['threshold_results'].items():
            status = "✓ PASS" if passed else "✗ FAIL"
            threshold_value = data['thresholds'].get(check, 'N/A')
            metric_name = check.replace('min_', '').replace('max_', '')
            actual_value = data['metrics'].get(metric_name, 0)
            f.write(f"- **{check}**: {status} (threshold: {threshold_value}, actual: {actual_value:.1f})\n")

        f.write("\n## Summary\n\n")
        all_passed = all(data['threshold_results'].values())
        if all_passed:
            f.write("✓ All thresholds passed. Judge is reliable.\n")
        else:
            f.write("✗ Some thresholds failed. Judge may need tuning.\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m eval_harness.calibrate --config <config_path>")
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

    # Run calibration
    try:
        run_calibration(config_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
