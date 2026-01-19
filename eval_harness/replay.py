"""
Failure replay functionality.
"""
import sys
import yaml
import json
from pathlib import Path
from .config import load_config
from .dataset_loader import load_dataset
from .prompt_builder import build_candidate_prompt
from .providers.factory import create_provider
from .hard_checks.runner import HardCheckRunner
from .utils.seed import set_seed
from .utils.logging import setup_logging


def replay_case(case_id: str, artifact_dir: str):
    """
    Replay a specific case from an artifact directory.

    Args:
        case_id: Case ID to replay
        artifact_dir: Path to artifact directory
    """
    logger = setup_logging()
    artifact_path = Path(artifact_dir)

    if not artifact_path.exists():
        raise ValueError(f"Artifact directory not found: {artifact_dir}")

    # Load config snapshot
    config_path = artifact_path / "config.yaml"
    if not config_path.exists():
        raise ValueError(f"Config snapshot not found: {config_path}")

    logger.info(f"Loading config from {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Load dataset
    dataset_path = config['dataset_path']
    logger.info(f"Loading dataset from {dataset_path}")
    cases = load_dataset(dataset_path)

    # Find the case
    case = None
    for c in cases:
        if c.id == case_id:
            case = c
            break

    if case is None:
        raise ValueError(f"Case {case_id} not found in dataset")

    logger.info(f"Found case: {case.id}")

    # Set seed
    seed = config.get('reproducibility', {}).get('seed', 1337)
    set_seed(seed)

    # Initialize providers
    logger.info("Initializing providers...")
    provider_a = create_provider(
        config['candidates']['A']['provider'],
        config['candidates']['A']['model']
    )
    provider_b = create_provider(
        config['candidates']['B']['provider'],
        config['candidates']['B']['model']
    )

    # Initialize hard check runner
    hard_check_runner = HardCheckRunner(config.get('hard_checks', {}))

    # Replay outputs
    logger.info("Replaying case...")

    outputs = {}
    for candidate, provider in [('A', provider_a), ('B', provider_b)]:
        logger.info(f"  Generating output from candidate {candidate}")

        # Build prompt
        prompt = build_candidate_prompt(case)

        # Generate
        try:
            output = provider.generate(prompt)
            outputs[candidate] = output

            # Run hard checks
            results = hard_check_runner.run_checks(output, case)
            has_failures = hard_check_runner.has_failures(results)

            logger.info(f"  Candidate {candidate}: {'FAILED' if has_failures else 'PASSED'} hard checks")

            for result in results:
                if not result.passed:
                    logger.warning(f"    {result.name}: {result.reason}")

        except Exception as e:
            logger.error(f"  Error: {e}")
            outputs[candidate] = f"ERROR: {e}"

    # Load original outputs if available
    outputs_path = artifact_path / "outputs.jsonl"
    original_outputs = {}

    if outputs_path.exists():
        logger.info("Loading original outputs for comparison...")
        with open(outputs_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                if data['case_id'] == case_id:
                    original_outputs = {
                        'A': data.get('output_a', ''),
                        'B': data.get('output_b', '')
                    }
                    break

    # Compare
    logger.info("=" * 60)
    logger.info("REPLAY RESULTS")
    logger.info("=" * 60)

    for candidate in ['A', 'B']:
        logger.info(f"\nCandidate {candidate}:")
        logger.info(f"Replayed Output: {outputs.get(candidate, 'N/A')[:100]}...")

        if original_outputs:
            original = original_outputs.get(candidate, '')
            logger.info(f"Original Output: {original[:100]}...")

            if outputs.get(candidate) == original:
                logger.info("✓ Outputs match")
            else:
                logger.warning("✗ Outputs differ")

    logger.info("=" * 60)


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python -m eval_harness.replay --case_id <id> --artifact_dir <path>")
        sys.exit(1)

    # Parse arguments
    case_id = None
    artifact_dir = None

    if '--case_id' in sys.argv:
        idx = sys.argv.index('--case_id')
        if idx + 1 < len(sys.argv):
            case_id = sys.argv[idx + 1]

    if '--artifact_dir' in sys.argv:
        idx = sys.argv.index('--artifact_dir')
        if idx + 1 < len(sys.argv):
            artifact_dir = sys.argv[idx + 1]

    if not case_id or not artifact_dir:
        print("Error: Both --case_id and --artifact_dir are required")
        sys.exit(1)

    # Run replay
    try:
        replay_case(case_id, artifact_dir)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
