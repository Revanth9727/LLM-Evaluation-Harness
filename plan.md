# LLM-Eval-Harness v1 Build Plan (to PyPI)

## Goal
Ship a focused, pairwise A/B regression-gating library to PyPI with clear BYO contracts (models, dataset, judge) and strong release hygiene.

## Principles
- Keep scope narrow: rigor over platform features.
- Preserve existing behavior while introducing callable-first interfaces.
- Prefer additive refactors and compatibility shims over rewrites.
- Every milestone ends with executable verification.

## Milestones

### 1) Freeze contracts and acceptance criteria
**Deliverables**
- Validate final PyPI package name availability before coding; rename early if needed.
- `PROJECT.md` treated as source-of-truth for v1 decisions.
- Dataset contract confirmed (`JSONL`, required `id` + `input`/`question`).
- Callable contract confirmed (model/judge signatures and error semantics).

**Verification**
- Self-review and commit on `PROJECT.md` and this plan.

---

### 2) Introduce callable-first runtime path
**Tasks**
- Add model callable adapter interface in core runner.
- Add judge callable adapter path.
- Define YAML callable import path (`module.submodule:function_name`) with exactly one of `provider` or `callable` per candidate/judge config.
- Add one boundary normalization function that converts raw model callable returns to canonical response shape.
- Route existing provider-based configs through adapter wrappers.
- Keep existing config shape working to avoid breakage.

**Files likely touched**
- `eval_harness/run.py`
- `eval_harness/providers/factory.py`
- new adapter module(s) under `eval_harness/providers/` or `eval_harness/runtime/`

**Verification**
- Existing smoke mock run still passes.
- New callable path can run A/B with in-memory stub functions.

---

### 3) Add tests for the new contract seams
**Tasks**
- Unit test model callable happy path.
- Unit test model callable string return normalization at boundary.
- Unit test model callable exception path (artifact records failure).
- Unit test judge callable happy path.
- Unit test judge callable exception path (pipeline continues).
- Unit test tie vs uncertain semantics (`tie` counted, `uncertain` excluded from win-rate denominator and eligible for retry/two-pass handling).
- Unit test backward compatibility for provider configs.

**Files likely touched**
- `tests/` (new test module + minor updates)

**Verification**
- `pytest tests -v` passes with new and existing tests.

---

### 4) Package cleanup for PyPI
**Tasks**
- Move `pytest` / `pytest-cov` out of core dependencies into dev extras.
- Make `pyproject.toml` the dependency source of truth; keep `requirements.txt` only as derived/dev convenience or remove it.
- Add `[project.scripts]` entry point (e.g., `eval-harness = eval_harness.cli:main`).
- Add metadata: authors, license, classifiers, keywords, URLs.
- Decide Python support and document explicitly.

**Files likely touched**
- `pyproject.toml`
- add `eval_harness/cli.py` (or equivalent)
- `README.md`

**Verification**
- `python -m build`
- `python -m twine check dist/*`
- fresh venv install + CLI launch command works.

---

### 5) CI packaging gate
**Tasks**
- Add CI job that builds wheel/sdist.
- Run `twine check` in CI.
- Add install-from-wheel smoke check in CI (same Python versions supported).

**Files likely touched**
- `.github/workflows/ci.yml`

**Verification**
- PR CI shows build + twine + install smoke all green.

---

### 6a) Early README contract pass (Priya-first)
**Tasks**
- Do first README rewrite early (right after contract lock) to surface unclear API seams before implementation hardens.
- Rewrite opening README section around the merge-time regression gate use case.
- Tighten language from “framework” to “regression gate”.
- Add explicit non-goals section.
- Document callable config entry (`provider` xor `callable`) and callable import string format.

**Files likely touched**
- `README.md`

**Verification**
- New user can understand contracts and run-path choices without reading source code.

---

### 6b) Final docs polish and examples
**Tasks**
- Document tie vs uncertain semantics explicitly for BYO judge implementers.
- Document that judge confidence is advisory and not used for bootstrap/gates.
- Document sync-only v1 behavior and expected runtime tradeoff.
- Add tiny dataset example in docs + `examples/` JSONL.
- Final quickstart and command validation pass.

**Files likely touched**
- `README.md`
- `examples/minimal_regression.jsonl`

**Verification**
- New user can follow README quickstart end-to-end without ambiguity.

---

### 7) Release plumbing
**Tasks**
- Add publish workflow (manual trigger acceptable for v1).
- Tag and publish initial release.

**Files likely touched**
- `.github/workflows/release.yml` (or equivalent)
- `pyproject.toml` (name/version as needed)

**Verification**
- `pip install <package>` in clean venv succeeds.
- `eval-harness --help` (or `eval-harness run ...`) works.

## Execution order (recommended)
1. Milestones 1 then 6a (lock contract and document it early)
2. Milestones 2–3 (runtime refactor + seam tests)
3. Milestones 4–5 (packaging + CI safeguards)
4. Milestones 6b–7 (final docs polish + release)

## Exit criteria
v1 is done when:
- Callable-first + provider-wrapper paths both work.
- Tests pass and cover seam failures.
- Build/twine/install are validated in CI.
- README clearly targets the Priya workflow.
- Package is published and installable on supported Python versions.
