# AI Agent Operating Guide
This section is the primary source of truth for how AI coding agents should understand, modify, and verify this repository.
It is intentionally human-readable and actionable.

---

## 1) Project Overview and Goal

**Project Name:** Project 1 — Eval Harness

**What this project does:**
A production-ready evaluation harness to compare **Candidate A vs Candidate B** (model/prompt/config) on a fixed task type.
It runs **deterministic Hard Checks first** (schema/citations/constraints) and uses an **LLM Judge only for subjective criteria**.
It produces reproducible artifacts and supports CI gating (smoke suite on PRs).

**Primary goal:**
Provide a consistent, reproducible, CI-gated mechanism to answer:
> "Is change B actually better than A, and can we prove it?"

**Non-goals (important):**
- Not building a full RAG debugger UI (that's Project 2 territory).
- Not optimizing for multiple unrelated task types in v1. Keep **one task type** as the baseline contract.

---

## 2) Technology Stack and Environment

**Language:** Python (target: 3.10+ recommended)
**Evaluation approach:** In-repo pairwise A/B regression harness
**Testing:** pytest
**CI:** GitHub Actions
**Data formats:** JSONL (datasets), YAML (configs), Markdown (docs), JSON/MD artifacts

**Package/venv:**
- Prefer `python -m venv .venv` and `pip install .[dev]`.
- Treat `pyproject.toml` as the dependency source of truth; `requirements.txt` is runtime convenience only.

**Environment variables (typical):**
- `OPENAI_API_KEY` (or other provider keys if used)
- `EVAL_SEED` (optional override)
- Any provider/model routing variables (document in `.env.example` if present)

---

## 3) Repository Structure

Current layout:
- `eval_harness/` — package code for the runner, checks, judge, metrics, artifacts, providers, callables, replay, calibration, and metamorphic tests
- `tests/` — pytest suites
- `data/` — JSONL evaluation datasets
- `configs/` — YAML configs for runs, calibration, and metamorphic checks
- `examples/` — small example datasets
- `artifacts/` — generated run outputs
- `scripts/` — helper scripts
- `PROJECT.md`, `README.md`, `HOW_TO_RUN.md`, `changes.md`, `plan.md` — project docs and release planning

Key modules:
- `eval_harness/run.py` — main pairwise evaluation pipeline
- `eval_harness/cli.py` — `eval-harness` console entry point
- `eval_harness/runtime/callables.py` — BYO callable loading and response normalization
- `eval_harness/hard_checks/` — deterministic checks
- `eval_harness/judge/` — judge prompt builder and runner
- `eval_harness/artifacts/` — artifact writer
- `eval_harness/calibrate.py` — judge calibration
- `eval_harness/metamorphic/` — transforms, invariants, and runner
- `eval_harness/replay.py` — failure replay

---

## 4) Core Principles (how to work in this repo)

1. **Hard Checks first; Judge last**
   - If something can be checked deterministically, do it in code.
   - Reserve judge calls for subjective criteria only.

2. **Reproducibility is a feature**
   - Changes must keep runs repeatable (seeded, stable configs, saved artifacts).
   - Every run must save enough metadata to reproduce later.

3. **Artifacts over opinions**
   - Any claim of improvement must be backed by a report folder and summary.

4. **CI is the gate**
   - A PR must not reduce smoke-suite quality or break the judge health check.

5. **Newbie-friendly**
   - Prefer clarity and explicitness over cleverness.
   - Add docs/runbooks when behavior isn't obvious.

---

## 5) Coding Guidelines and Standards

**General:**
- Write small, testable functions.
- Prefer explicit types and clear names.
- Keep "business logic" out of notebooks; notebooks are for exploration only.

**Python style:**
- Use type hints on public functions.
- Docstrings required for public modules/classes/functions:
  - Purpose
  - Inputs/outputs
  - Exceptions/edge cases
- Avoid hidden global state; config should be passed in explicitly.

**Determinism:**
- Seed all RNG sources used (python `random`, numpy if used, judge order randomization seeds).
- Log the seed and config snapshot into artifacts.

**Logging:**
- Use structured logging where possible (JSON logs are ideal).
- Never log secrets (API keys).

**Data handling:**
- Do not edit canonical datasets casually.
- If dataset changes are necessary, include:
  - rationale
  - version bump
  - changelog entry
  - before/after stats

---

## 6) Common Commands and Workflows

### Setup
- `python -m venv .venv && source .venv/bin/activate`
- `pip install .[dev]`

### Lint / type-check (if configured)
- `make lint`
- `make format` (if formatter configured)

### Unit tests
- `pytest -q`

### Smoke eval (CI default)
- `make smoke-mock`
  Runs the mock-provider smoke dataset with no API calls.

### Full evaluation run
- `python -m eval_harness.run --config configs/regression.yaml`
- `eval-harness run --config configs/regression.yaml`

### Judge calibration
- `python -m eval_harness.calibrate --config configs/judge_calibration.yaml`
- `eval-harness calibrate --config configs/judge_calibration.yaml`

### Metamorphic suite
- `python -m eval_harness.metamorphic.run --config configs/metamorphic.yaml`
- `eval-harness metamorphic --config configs/metamorphic.yaml`

### Replay a failure
- `python -m eval_harness.replay --case_id <ID> --artifact_dir <path>`
- `eval-harness replay --case_id <ID> --artifact_dir <path>`

**Git workflow:**
- Feature branches: `feature/<short-name>` or `fix/<short-name>`
- Keep PRs small and include the report artifact summary when behavior changes.

---

## 7) Verification and Testing Instructions

When changes impact evaluation results:

1. **Run unit tests**
   - `pytest -q`
   - Expect: all tests pass.

2. **Run smoke suite**
   - `make smoke-mock` for no-cost CI wiring checks.
   - `make smoke` when real provider credentials are configured.
   - Expect: no regressions vs baseline thresholds.

3. **If judge/rubric/prompt changed, run judge calibration**
   - Generate or update reliability report.
   - Ensure judge health check thresholds still pass.

4. **If transforms or invariants changed, run metamorphic suite**
   - Ensure invariants remain meaningful and stable.

5. **Check artifacts**
   - Confirm `outputs.jsonl`, `hard_checks.jsonl`, `judge_votes.jsonl`, `summary.md`, `summary.json`, `config.yaml`, `cases.jsonl`, and `run_meta.json` exist when applicable.
   - Confirm artifact folder includes config snapshot and seed.

If any step fails, fix and rerun before declaring done.

---

## 8) How AI Agents Should Make Changes

**Before coding:**
- Identify the smallest change that satisfies the task.
- State assumptions explicitly in the PR description or summary.

**During implementation:**
- Prefer incremental commits (or clearly separated changes).
- Keep interfaces stable: dataset schema, report schema, CLI flags.

**After implementation:**
- Update docs if behavior changes:
  - `README.md`
  - `HOW_TO_RUN.md`
  - `PROJECT.md` or `changes.md` when contracts or release status change
  - example configs

**Avoid:**
- Introducing non-deterministic behavior (unseeded randomness, time-based ordering).
- Silent dataset or rubric changes without versioning.
- Large refactors without tests.

---

## 9) Troubleshooting and Known Issues

Common issues:
- **`ModuleNotFoundError`**
  - Ensure venv is active and dependencies installed.
- **Provider auth errors**
  - Confirm relevant API key env var is set.
- **Flaky judge results**
  - Verify:
    - A/B order randomization is enabled and logged
    - 2-pass judging for stability is enabled
    - calibration thresholds are reasonable
- **Artifact mismatch / missing fields**
  - Ensure run writes config snapshot and outputs consistently.

---

## 10) External Documentation

Avoid embedding large docs here; instead treat the files below as the operating manual for this repo.

**Acceptance / contracts:**
- `PROJECT.md` — v1 scope, user, BYO callable contract, outcome semantics, and PyPI definition of done
- `README.md` — user-facing quickstart, architecture, config example, and release checklist
- `plan.md` — milestone execution plan
- `changes.md` — current release-prep change summary

**How to run + how to debug:**
- `HOW_TO_RUN.md` — beginner runbook for setup, smoke, regression, calibration, metamorphic tests, replay, and artifacts
- `artifacts/artifacts_spec.md` — artifact schema reference

---

## 11) Maintaining This File

This is a living document:
- Update it when repo structure, commands, or standards change.
- Keep it concise and practical; optimize for "a new team member can succeed quickly."

---
