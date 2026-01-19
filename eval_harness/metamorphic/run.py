"""
Metamorphic testing runner.
"""
import sys
import json
import random
from pathlib import Path
from typing import Dict, List, Any
from ..config import load_config
from ..dataset_loader import load_dataset
from ..prompt_builder import build_candidate_prompt
from ..providers.factory import create_provider
from ..hard_checks.runner import HardCheckRunner
from ..artifacts.writer import create_run_id
from ..utils.seed import set_seed
from ..utils.logging import setup_logging
from .transforms.reorder_context import ReorderContextTransform
from .transforms.remove_key_chunk import RemoveKeyChunkTransform
from .transforms.paraphrase_question import ParaphraseQuestionTransform
from .transforms.add_irrelevant_doc import AddIrrelevantDocTransform
from .invariants.citations_present import CitationsPresentInvariant
from .invariants.idk_when_missing import IDKWhenMissingInvariant


def run_metamorphic(config_path: str):
    """
    Run metamorphic testing.

    Args:
        config_path: Path to config file
    """
    logger = setup_logging()
    logger.info(f"Loading metamorphic config from {config_path}")

    # Load config
    config = load_config(config_path)

    # Set seed
    seed = config.get('reproducibility', {}).get('seed', 1337)
    set_seed(seed)

    # Load base dataset
    dataset_path = config['base_dataset_path']
    logger.info(f"Loading base dataset from {dataset_path}")
    cases = load_dataset(dataset_path)
    logger.info(f"Loaded {len(cases)} cases")

    # Initialize provider (use candidate A for metamorphic testing)
    # For simplicity, we'll use a single candidate
    logger.info("Initializing provider...")
    provider = create_provider("mock", "mock")  # Use mock for demo

    # Initialize hard check runner
    hard_check_runner = HardCheckRunner(config.get('hard_checks', {}))

    # Initialize transforms
    transforms = []
    transform_configs = config.get('transforms', [])
    for t_config in transform_configs:
        if not t_config.get('enabled', True):
            continue

        name = t_config['name']
        if name == 'reorder_context':
            transforms.append(('reorder_context', ReorderContextTransform()))
        elif name == 'remove_key_chunk':
            transforms.append(('remove_key_chunk', RemoveKeyChunkTransform()))
        elif name == 'paraphrase_question':
            transforms.append(('paraphrase_question', ParaphraseQuestionTransform()))
        elif name == 'add_irrelevant_doc':
            transforms.append(('add_irrelevant_doc', AddIrrelevantDocTransform()))

    logger.info(f"Loaded {len(transforms)} transforms")

    # Initialize invariants
    invariants = []
    invariant_configs = config.get('invariants', [])
    task_contract = config.get('task_contract', {})

    for inv_config in invariant_configs:
        name = inv_config['name']
        if name == 'citations_present_when_required':
            invariants.append(('citations_present', CitationsPresentInvariant(inv_config)))
        elif name == 'idk_when_missing_context':
            invariants.append(('idk_when_missing', IDKWhenMissingInvariant(inv_config)))

    logger.info(f"Loaded {len(invariants)} invariants")

    # Run metamorphic tests
    results = []

    for i, case in enumerate(cases, 1):
        logger.info(f"[{i}/{len(cases)}] Processing case {case.id}")

        # Generate baseline output
        prompt = build_candidate_prompt(case)
        original_output = provider.generate(prompt)

        # Run hard checks on original
        original_checks = hard_check_runner.run_checks(original_output, case)
        original_passed = not hard_check_runner.has_failures(original_checks)

        case_results = {
            'case_id': case.id,
            'original_output': original_output,
            'original_passed_hard_checks': original_passed,
            'transforms': []
        }

        # Apply each transform
        for transform_name, transform in transforms:
            logger.info(f"  Applying transform: {transform_name}")

            # Transform case
            transformed_case = transform.transform(case)

            # Generate output for transformed case
            transformed_prompt = build_candidate_prompt(transformed_case)
            transformed_output = provider.generate(transformed_prompt)

            # Run hard checks on transformed
            transformed_checks = hard_check_runner.run_checks(transformed_output, transformed_case)
            transformed_passed = not hard_check_runner.has_failures(transformed_checks)

            # Check invariants
            invariant_results = {}
            for inv_name, invariant in invariants:
                holds = invariant.check(case, transformed_case, original_output, transformed_output)
                invariant_results[inv_name] = holds

            case_results['transforms'].append({
                'transform': transform_name,
                'transformed_output': transformed_output,
                'transformed_passed_hard_checks': transformed_passed,
                'invariants': invariant_results
            })

        results.append(case_results)

    # Calculate summary statistics
    logger.info("Calculating summary statistics...")

    total_transforms = sum(len(r['transforms']) for r in results)
    total_invariants = total_transforms * len(invariants) if invariants else 0

    invariants_passed = 0
    for result in results:
        for transform_result in result['transforms']:
            for inv_name, holds in transform_result['invariants'].items():
                if holds:
                    invariants_passed += 1

    robustness_score = (invariants_passed / total_invariants * 100) if total_invariants > 0 else 0

    # Per-transform breakdown
    transform_stats = {}
    for transform_name, _ in transforms:
        transform_invariants_total = 0
        transform_invariants_passed = 0

        for result in results:
            for transform_result in result['transforms']:
                if transform_result['transform'] == transform_name:
                    for inv_name, holds in transform_result['invariants'].items():
                        transform_invariants_total += 1
                        if holds:
                            transform_invariants_passed += 1

        transform_stats[transform_name] = {
            'total': transform_invariants_total,
            'passed': transform_invariants_passed,
            'pass_rate': (transform_invariants_passed / transform_invariants_total * 100)
                        if transform_invariants_total > 0 else 0
        }

    # Write artifacts
    run_id = create_run_id(config.get('run_name', 'metamorphic'))
    artifacts_root = Path(config.get('artifacts', {}).get('root_dir', 'artifacts'))
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing artifacts to {run_dir}")

    # Write metamorphic_results.json
    results_data = {
        'summary': {
            'total_cases': len(cases),
            'total_transforms': total_transforms,
            'total_invariants_checked': total_invariants,
            'invariants_passed': invariants_passed,
            'robustness_score': robustness_score
        },
        'per_transform': transform_stats,
        'cases': results
    }

    with open(run_dir / 'metamorphic_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)

    # Write metamorphic_summary.md
    with open(run_dir / 'metamorphic_summary.md', 'w') as f:
        f.write("# Metamorphic Testing Summary\n\n")
        f.write(f"**Robustness Score:** {robustness_score:.1f}%\n\n")
        f.write(f"- Total Cases: {len(cases)}\n")
        f.write(f"- Total Transforms: {total_transforms}\n")
        f.write(f"- Total Invariants Checked: {total_invariants}\n")
        f.write(f"- Invariants Passed: {invariants_passed}\n\n")

        f.write("## Per-Transform Breakdown\n\n")
        for transform_name, stats in transform_stats.items():
            f.write(f"### {transform_name}\n\n")
            f.write(f"- Pass Rate: {stats['pass_rate']:.1f}%\n")
            f.write(f"- Passed: {stats['passed']}/{stats['total']}\n\n")

    # Write outputs_transformed.jsonl
    with open(run_dir / 'outputs_transformed.jsonl', 'w') as f:
        for result in results:
            output_line = {
                'case_id': result['case_id'],
                'original_output': result['original_output'],
                'transforms': {}
            }
            for transform_result in result['transforms']:
                output_line['transforms'][transform_result['transform']] = {
                    'output': transform_result['transformed_output'],
                    'invariants': transform_result['invariants']
                }
            f.write(json.dumps(output_line) + '\n')

    logger.info("=" * 60)
    logger.info(f"Metamorphic Testing Complete!")
    logger.info(f"Robustness Score: {robustness_score:.1f}%")
    logger.info("=" * 60)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m eval_harness.metamorphic --config <config_path>")
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

    # Run metamorphic testing
    try:
        run_metamorphic(config_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
