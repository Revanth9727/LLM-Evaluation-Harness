# CLAUDE.md — Project 1 (Eval Harness) AI Constitution

This file is the **primary source of truth** for how Claude Code should understand, modify, and verify this repository.  
It is intentionally **human-readable** and **actionable**.

---

## 1) Project Overview and Goal

**Project Name:** Project 1 — Eval Harness

**What this project does:**  
A production-ready evaluation harness to compare **Candidate A vs Candidate B** (model/prompt/config) on a fixed task type.  
It runs **deterministic Hard Checks first** (schema/citations/constraints) and uses an **LLM Judge only for subjective criteria**.  
It produces reproducible artifacts and supports CI gating (smoke suite on PRs).

**Primary goal:**  
Provide a consistent, reproducible, CI-gated mechanism to answer:  
> “Is change B actually better than A, and can we prove it?”

**Non-goals (important):**
- Not building a full RAG debugger UI (that’s Project 2 territory).
- Not optimizing for multiple unrelated task types in v1. Keep **one task type** as the baseline contract.

---

## 2) Technology Stack and Environment

**Language:** Python (target: 3.10+ recommended)  
**Evaluation framework:** DeepEval  
**Testing:** pytest  
**CI:** GitHub Actions  
**Data formats:** JSONL (datasets), YAML (configs), Markdown (docs), JSON/MD/HTML (reports)

**Package/venv:**
- Prefer `python -m venv .venv` and `pip install -r requirements.txt` (or equivalent used in repo).
- Keep dependencies pinned for reproducibility.

**Environment variables (typical):**
- `OPENAI_API_KEY` (or other provider keys if used)
- `EVAL_SEED` (optional override)
- Any provider/model routing variables (document in `.env.example` if present)

---

## 3) Repository Structure (expected)

> If the repo differs, update this section to match reality.

Recommended layout:
- `src/` — harness code (runner, checks, judge, reporting)
- `tests/` — pytest + DeepEval tests
- `datasets/` or `data/` — JSONL datasets
- `configs/` — YAML configs for runs (A/B definition, seeds, thresholds)
- `docs/` — documentation (this file, design notes, runbooks)
- `artifacts/` or `reports/` — run outputs (timestamp + git SHA)
- `scripts/` — helper scripts (calibration, metamorphic, replay)

Key modules (conceptual):
- `harness/run.py` — main entrypoint (CLI)
- `harness/checks/` — Hard Checks
- `harness/judge/` — judging prompts/rubrics/exemplars + runner
- `harness/calibration/` — judge reliability + health check
- `harness/metamorphic/` — transformations + invariants
- `harness/replay.py` — failure replay

---

## 4) Core Principles (how to work in this repo)

1) **Hard Checks first; Judge last**  
   - If something can be checked deterministically, do it in code.
   - Reserve judge calls for subjective criteria only.

2) **Reproducibility is a feature**  
   - Changes must keep runs repeatable (seeded, stable configs, saved artifacts).
   - Every run must save enough metadata to reproduce later.

3) **Artifacts over opinions**  
   - Any claim of improvement must be backed by a report folder and summary.

4) **CI is the gate**  
   - A PR must not reduce smoke-suite quality or break the judge health check.

5) **Newbie-friendly**  
   - Prefer clarity and explicitness over cleverness.
   - Add docs/runbooks when behavior isn’t obvious.

---

## 5) Coding Guidelines and Standards

**General:**
- Write small, testable functions.
- Prefer explicit types and clear names.
- Keep “business logic” out of notebooks; notebooks are for exploration only.

**Python style:**
- Use type hints on public functions.
- Docstrings required for public modules/classes/functions:
  - Purpose
  - Inputs/outputs
  - Exceptions/edge cases
- Avoid hidden global state; config should be passed in explicitly.

**Determinism:**
- Seed all RNG sources used (python `random`, numpy if used, framework seeds).
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

> Replace/extend these if the repo uses different tooling.

### Setup
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt`

### Lint / type-check (if configured)
- `make lint`  
- `make format` (if formatter configured)

### Unit tests
- `pytest -q`

### Smoke eval (CI default)
- `make smoke`  
  Runs a small dataset (10–15 cases) to detect regressions quickly.

### Full evaluation run
- `python -m harness.run --config configs/baseline.yaml`

### Judge calibration
- `python -m harness.calibration.run --config configs/judge_calibration.yaml`

### Metamorphic suite
- `python -m harness.metamorphic.run --config configs/metamorphic.yaml`

### Replay a failure
- `python -m harness.replay --case_id <ID> --artifact_dir <path>`

**Git workflow:**
- Feature branches: `feature/<short-name>` or `fix/<short-name>`
- Keep PRs small and include the report artifact summary when behavior changes.

---

## 7) Verification and Testing Instructions (Claude must follow)

When you (Claude) make changes that impact evaluation results:

1) **Run unit tests**
   - `pytest -q`
   - Expect: all tests pass.

2) **Run smoke suite**
   - `make smoke` (or the repo’s defined smoke command)
   - Expect: no regressions vs baseline thresholds.

3) **If judge/rubric/prompt changed → run judge calibration**
   - Generate or update reliability report.
   - Ensure judge health check thresholds still pass.

4) **If transforms or invariants changed → run metamorphic suite**
   - Ensure invariants remain meaningful and stable.

5) **Check artifacts**
   - Confirm `outputs.jsonl`, `hard_checks.json`, `judge_votes.json`, `summary.md` (or repo equivalents) exist.
   - Confirm artifact folder includes config snapshot and seed.

If any step fails, fix and re-run before declaring done.

---

## 8) How Claude Should Make Changes (behavior rules)

**Before coding:**
- Identify the smallest change that satisfies the task.
- State assumptions explicitly in the PR description or summary.

**During implementation:**
- Prefer incremental commits (or clearly separated changes).
- Keep interfaces stable: dataset schema, report schema, CLI flags.

**After implementation:**
- Update docs if behavior changes:
  - `README.md`
  - `docs/` runbooks
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

## 10) External Documentation (keep concise)

Avoid embedding large docs here; instead treat the files below as the “operating manual” for this repo.

**Acceptance / contracts (binding):**
- `docs/PROJECT_CHECKLIST.md` — Definition of Done + CI exit criteria
- `docs/task_contract.md` — what “passing” means for Citation Q&A (v1)
- `docs/hard_checks.md` — deterministic gates; judge must be skipped on hard-check failures
- `docs/judge_rubric.md` — how the judge compares A vs B (subjective only)

**How to run + how to debug:**
- `docs/project1_eval_harness.md` — full project explanation (newbie-friendly)
- `docs/runbook_interpreting_reports.md` — how to read artifacts and respond to failures

**Reliability + robustness skills:**
- `docs/judge_calibration.md` — methodology, metrics, thresholds, CI healthcheck behavior
- `docs/metamorphic_testing.md` — transforms, invariants, scoring, expected artifacts


## 11) Maintaining This File

This is a living document:
- Update it when repo structure, commands, or standards change.
- Keep it concise and practical—optimize for “a new team member can succeed quickly.”
