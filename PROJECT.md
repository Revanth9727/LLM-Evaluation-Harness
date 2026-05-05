# LLM-Eval-Harness — Project Brief (v1 to PyPI)

## What this project is

A regression-test harness for doc-grounded LLM assistants. It is opinionated about one workflow: pairwise A vs B comparison of model or prompt changes, run by an engineer who is about to merge a change and needs a pass/fail signal stronger than vibes.

It is not a general-purpose eval framework. It is not a dashboard. It is not a benchmarking platform.

## Who it's for

The user is a senior or staff ML engineer at a company shipping a doc-grounded LLM assistant where wrong answers have real consequences — fintech, healthtech, legal, internal enterprise tools. They own a regular cadence of prompt or model changes. They have CI. They are tired of "it felt better when I tried it" being the bar for shipping.

The user reaches for the tool at the moment of merging a change. They want a fast, statistically rigorous answer to: "is version B actually better than version A on my regression set?"

## What the user brings

- Their own model versions (model A and model B), wired up and callable
- Their own regression dataset
- Their own judge access (OpenAI or Anthropic API key)

The tool does not provide production datasets, provider account setup, or judge access. It assumes a serious user who has these things ready.

## What the tool owns

The rigor of the comparison itself:
- Deterministic checks first (format, citations, refusal behavior) to filter out cheap mechanical failures before any judging
- LLM-as-judge with rubric scoring on the surviving cases
- Position-bias mitigation via A/B order randomization and optional two-pass judging
- Bootstrap confidence intervals on the win rate
- A CI-friendly exit code (`0` pass / `2` fail) so the tool can gate merges

## Current state of the codebase

- A vs B regression pipeline already works end-to-end (`eval_harness/run.py`): load cases → run candidate A/B → hard checks → optional judge → metrics/CI/gates → exit code
- Provider-specific adapters (`openai_provider.py`, `mock_provider.py`, `factory.py`) exist alongside the new callable-first runtime path
- README is mostly aligned with the Priya framing — uses "pairwise A/B," "CI gate," "deterministic checks first," "bootstrap CI" language
- Some "framework"-style language remains that should be tightened to "regression gate for model/prompt changes"
- Packaging gaps exist (per earlier audit): pytest in main deps, no console entry point, missing project metadata, Python 3.10+ gate not clearly documented, no PyPI release workflow, CI doesn't validate the packaging install path

## Callable interface contract (resolved)

For v1, add a BYO callable path with the smallest practical contract.

### Model callable (candidate A/B)

Each candidate provides a Python callable with this shape:

```python
def model_fn(*, input: str, context: list | None = None, metadata: dict | None = None) -> dict | str:
    ...
```

Rules:
- `input` is required and is the user question/prompt from dataset row.
- `context` is optional and passed through unchanged from the case.
- `metadata` is optional and contains non-core row fields (`case.extra`) for user-specific logic.
- Preferred return is a dict with required `output: str` and optional metadata (for example `citations`, `latency_ms`, `token_usage`, `model_id`, `metadata`).
- String returns are accepted only at the boundary and normalized once to `{"output": <string>}`.
- The `dict | str` union is external-only at callable ingress; inside the harness all model responses use one canonical `ModelResponse` shape.
- Any exception is treated as candidate failure for that case and captured in artifacts.

### Judge callable

Optional judge callable:

```python
def judge_fn(*, prompt: str, metadata: dict | None = None) -> dict:
    ...
```

Rules:
- Input is the already-built judge prompt string.
- Return is structured with required `winner` where `winner` is one of `"A" | "B" | "tie" | "uncertain"`.
- `tie` means the judge compared both and found them equal.
- `uncertain` means the judge could not make a reliable comparison.
- Optional fields: `confidence`, `reasons`, `citations_assessed`, `notes`, `raw_response`.
- `confidence` is advisory metadata only; it is not used for bootstrap statistics or gate decisions.
- Judge exceptions mark verdict as unavailable for that case; pipeline continues.

### Timeouts, retries, and errors

- v1 keeps timeout policy in pipeline/config, not in callable signature.
- Callables remain sync for v1 (async out of scope).
- Error normalization happens centrally in harness runner.
- Two-pass/retry logic is triggered by verdict state (`uncertain` or parse/error conditions), not by numeric confidence.
- Two-pass uses the same judge with swapped A/B order and a different deterministic seed.
- If first and second pass disagree (or either pass is parse/error), final verdict is `uncertain`.

### Outcome semantics

- `A`, `B`, and `tie` are valid judged outcomes.
- `uncertain` is treated as non-decisive and excluded from the win-rate denominator.
- If all cases become non-judgeable after hard checks (or after judge uncertainty), the run fails closed by default with an explicit message.

### Backward compatibility

- Existing provider configs remain supported as thin wrappers that adapt to this callable contract.

## What v1 to PyPI looks like — definition of done

Each item is binary.

### Code
- BYO callable interface added: `eval_harness` accepts a Python callable as the model, alongside existing provider configs
- Existing OpenAI/Anthropic providers remain as thin convenience wrappers over the callable interface
- One tiny example JSONL in `examples/` (5–10 rows) as a format reference

### Packaging
- Move `pytest` and `pytest-cov` from main dependencies into `optional-dependencies.dev`
- Add a console entry point so `eval-harness run --config foo.yaml` works
- Add full project metadata: authors, license, classifiers, keywords, project URLs
- Decide and document Python version support
- Verify package name availability on PyPI; pick a different name if unavailable
- Add a CI job that builds wheel/sdist and runs `twine check` on every PR

### Positioning and docs
- README first paragraph reframed around the Priya use case
- Tighten remaining "framework" language
- Quickstart assumes user has models, data, and judge ready
- Add a "what this is not" section listing non-goals

### Release
- PyPI release workflow set up (manual is fine for v1)
- Successfully publish `0.1.0` to PyPI (or next version if name/version changes)
- Verify `pip install` works in a clean venv on supported Python versions

## Explicitly out of scope for v1

- Embedding-based or learned classifiers for judging
- Multi-model A/B/C support beyond pairwise
- Dashboards or web UI
- Auto-dataset generation
- New provider adapters beyond existing set
- Plugin system, broad integrations, marketing site

## Time budget

Two weekends of focused work. If this stretches into a third weekend, pause and reassess scope vs a core bug.

## Why this scope is the right one

Most eval frameworks try to be everything to everyone. The value here is the opposite: one sharp workflow, one defensible decision signal, minimal surface area, fast path to a useful release.
