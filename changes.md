# Changes Summary

This document summarizes all major updates completed to prepare `LLM-Evaluation-Harness` for PyPI release and BYO callable workflows.

## 1) Runtime + Contract Updates

- Added callable-first runtime support for candidates and judge.
- Implemented callable loader + boundary normalization in `eval_harness/runtime/callables.py`.
- Added canonical internal `ModelResponse` in `eval_harness/models.py`.
- Updated evaluation pipeline (`eval_harness/run.py`) to:
  - support provider or callable candidates,
  - support provider or callable judge,
  - normalize callable outputs at the boundary,
  - preserve metadata in outputs,
  - fail closed when gates are enabled but no decisive outcomes exist.
- Updated judge runner (`eval_harness/judge/runner.py`) to:
  - accept structured judge callable responses,
  - enforce winner contract (`A|B|tie|uncertain`),
  - trigger two-pass retry on `uncertain` verdict state,
  - treat `confidence` as advisory only.

## 2) Config Validation Updates

- Extended run-config validation in `eval_harness/config.py`:
  - each candidate must define exactly one of `provider` or `callable`,
  - enabled judge must define exactly one of `provider` or `callable`,
  - callable import path format is validated (`module:function`).

## 3) Test Coverage Additions

- Added callable seam fixtures in `tests/callable_fixtures.py`.
- Added/expanded callable contract tests in `tests/test_runtime_callables.py` for:
  - callable import path loading/validation,
  - model callable string normalization,
  - model callable dict normalization happy path,
  - missing `output` dict validation,
  - judge winner validation,
  - candidate/judge provider-vs-callable XOR config rules,
  - judge two-pass behavior on `uncertain`,
  - judge callable exception path,
  - candidate callable exception artifact path,
  - end-to-end run with candidate+judge callables,
  - provider backward-compat run path.

## 4) Packaging + CLI Updates

- Added CLI entrypoint implementation in `eval_harness/cli.py`.
- Added package console script (`eval-harness`) via `pyproject.toml`.
- Updated package metadata in `pyproject.toml`.
- Moved test/dev tooling dependencies into `optional-dependencies.dev`.
- Aligned `Makefile` setup flow to install from `pyproject.toml` (`pip install .[dev]`).
- Simplified `requirements.txt` to runtime dependencies only.

## 5) CI + Release Pipeline Updates

- Updated CI workflow in `.github/workflows/ci.yml` to:
  - install from `pyproject.toml`,
  - run tests,
  - run smoke checks,
  - build distributions,
  - run `twine check`,
  - install built wheel and verify CLI.
- Added manual release workflow for PyPI trusted publishing:
  - `.github/workflows/release.yml`.
- Added manual TestPyPI dry-run workflow:
  - `.github/workflows/release-testpypi.yml`.

## 6) Documentation + Examples

- Updated architecture/decision docs:
  - `PROJECT.md` (contracts, semantics, two-pass logic),
  - `plan.md` (milestone execution plan).
- Updated `README.md` to include:
  - merge-time regression gate framing,
  - BYO callable contract,
  - tie vs uncertain semantics,
  - confidence advisory behavior,
  - context payload behavior (list payload; oracle mode normalized chunks),
  - release dry-run checklist for TestPyPI.
- Added minimal example dataset:
  - `examples/minimal_regression.jsonl`.

## 7) Additional Hardening Fixes

- Fixed tag breakdown handling in artifact writer for cases with `tags: null`:
  - `eval_harness/artifacts/writer.py` now safely iterates `case.tags or []`.

## 8) Verification Performed

- Test suite executed successfully after updates:
  - `python3 -m pytest tests -q` → **54 passed**.
- Packaging checks passed:
  - `python -m build` → passed,
  - `python -m twine check dist/*` → passed.
- Built wheel install + CLI smoke verified:
  - `eval-harness --help` works from installed wheel.

---

If needed, this file can be split into:
1) `CHANGELOG.md` (user-facing release notes), and
2) `docs/release_checklist.md` (maintainer operational steps).
