"""Unified CLI entry point for eval-harness."""
import argparse
import sys

from .calibrate import run_calibration
from .metamorphic.run import run_metamorphic
from .replay import replay_case
from .run import run_evaluation


def main() -> None:
    """CLI entrypoint used by the `eval-harness` console script."""
    parser = argparse.ArgumentParser(prog="eval-harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run pairwise A/B evaluation")
    run_parser.add_argument("--config", required=True, help="Path to run config YAML")

    calibrate_parser = subparsers.add_parser("calibrate", help="Run judge calibration")
    calibrate_parser.add_argument("--config", required=True, help="Path to calibration config YAML")

    metamorphic_parser = subparsers.add_parser("metamorphic", help="Run metamorphic tests")
    metamorphic_parser.add_argument("--config", required=True, help="Path to metamorphic config YAML")

    replay_parser = subparsers.add_parser("replay", help="Replay one case from artifacts")
    replay_parser.add_argument("--case_id", required=True, help="Case ID to replay")
    replay_parser.add_argument("--artifact_dir", required=True, help="Artifact directory path")

    args = parser.parse_args()

    if args.command == "run":
        sys.exit(run_evaluation(args.config))
    if args.command == "calibrate":
        run_calibration(args.config)
        return
    if args.command == "metamorphic":
        run_metamorphic(args.config)
        return
    if args.command == "replay":
        replay_case(args.case_id, args.artifact_dir)
        return


if __name__ == "__main__":
    main()
