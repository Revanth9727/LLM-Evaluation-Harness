# Eval Harness

A merge-time regression gate for doc-grounded LLM assistants. You run candidate A vs B on your own regression set, enforce deterministic checks first, judge only what remains, and block merges with a `0/2` CI exit code backed by bootstrap confidence intervals.

## Why This Exists

Most LLM evaluation tools fall into two camps: hosted observability platforms (Langfuse, Braintrust) that require sending data to a third party, or open benchmark suites (lm-evaluation-harness, OpenAI Evals) designed for leaderboard rankings across standardized tasks. Neither answers the most common production question: *you changed a prompt or swapped a model — is it actually better?*

This harness takes an opinionated position: **deterministic checks first, LLM judge only for what remains.** Most quality failures in production — missing citations, format violations, hallucinated refusals — are fully detectable with regex and string matching. Spending judge tokens on them is waste. The judge runs only on the subjective remainder, with randomized A/B presentation order and optional two-pass judging to control for position bias.

The output is a single exit code — `0` or `2` — that your CI pipeline gates on, backed by bootstrap confidence intervals. Not vibes. Not a dashboard you check next Tuesday.

## Worked Example

Run the 40-case smoke suite with mock providers. No API keys, zero cost, under 3 seconds:

```
$ eval-harness run --config configs/smoke_mock.yaml

Loading config from configs/smoke_mock.yaml
Loaded 40 cases
[1/40] Processing case single_001
  Generating output from candidate A
  Generating output from candidate B
  Running judge...
  Judge verdict: tie (confidence: 0.00)
...
[31/40] Processing case out_001
  Candidate A failed hard checks
  Candidate B failed hard checks
  Skipping judge (hard check failures)
...
Evaluation complete! Artifacts written to artifacts/smoke_mock_20260426_223203_5c6b4f1
Summary: 40 cases, 30 judged
```

| Metric | Candidate A | Candidate B |
|---|---|---|
| Hard check failures | 10 / 40 | 10 / 40 |
| Format pass rate | 0.750 | 0.750 |
| Refusal rate | 0.000 | 0.000 |

| Judge Results | |
|---|---|
| Cases judged | 30 |
| Win rate (A) | 0.000 |
| 95% CI | [0.000, 0.000] |
| Gate decision | SKIPPED (gates disabled) |

The 10 hard check failures are by design — those cases are tagged `should_say_idk` (the model should refuse because the context doesn't contain the answer), and the mock provider doesn't produce the exact canonical refusal string. The judge never sees those cases. They're caught deterministically, which is the point.

With mock providers, all 30 judged cases return "tie" at 0.0 confidence — the mock judge is a no-op for CI wiring tests. In a real run with GPT-4o-mini judging GPT-4o vs Llama 3.1, you'd see actual winners, confidence scores, and a CI that tells you whether the win rate is statistically significant or just noise.

All artifacts land in `artifacts/smoke_mock_<timestamp>_<git_sha>/` — 8 files including config snapshot, per-case outputs, hard check results, judge votes, and both JSON and Markdown summaries.

## Quickstart

```bash
pip install eval-harness
eval-harness run --config configs/smoke_mock.yaml
```

Results print to stdout. Full artifacts write to `artifacts/`. Start with `summary.md` in the run folder.

When developing from a local checkout, use `pip install .[dev]`. The Makefile is a contributor convenience; the installed user interface is the `eval-harness` CLI.

## BYO Contract (v1)

The harness assumes you already have models, regression data, and judge access.

- For each candidate, config must define exactly one of `provider` or `callable`.
- Callable paths use `module.submodule:function_name` import strings.
- Candidate callable signature:
  - `def fn(*, input: str, context: list | None = None, metadata: dict | None = None) -> dict | str`
  - Preferred return is dict with required `output` key.
  - `context` is a Python list payload (not a JSON string). In non-oracle mode, it passes through dataset context. In oracle mode, it is a normalized list of chunk dicts.
- Judge callable signature:
  - `def fn(*, prompt: str, metadata: dict | None = None) -> dict`
  - Required: `winner` in `A | B | tie | uncertain`

Judge semantics:
- `tie` = both candidates judged equal quality.
- `uncertain` = judge could not make a reliable comparison.
- `uncertain` is excluded from win-rate denominator and is eligible for two-pass retry.
- `confidence` is advisory metadata only (not used for gating or bootstrap statistics).

## How It Works

```
Dataset (JSONL)
     │
     ├──► Candidate A ──► Hard Checks ──► pass? ──┐
     │                                             │
     └──► Candidate B ──► Hard Checks ──► pass? ──┤
                                                   │
                                            ┌──────▼──────┐
                                            │  LLM Judge  │
                                            │ (A/B swap,  │
                                            │  two-pass)  │
                                            └──────┬──────┘
                                                   │
                                            ┌──────▼──────┐
                                            │   Metrics   │
                                            │  win rate,  │
                                            │ bootstrap CI│
                                            └──────┬──────┘
                                                   │
                                            ┌──────▼──────┐
                                            │    Gates    │
                                            │  exit 0 / 2 │
                                            └─────────────┘
```

Each test case flows through two stages. **Stage 1** is deterministic: both candidates generate an answer, then seven hard checks (non-empty, citations present, canonical refusal, forbidden phrases, max length, latency budget, cost proxy) pass or fail the output with zero ambiguity. Failed outputs never reach the judge — most CI failures in production are format violations, not subtle quality differences, and catching them without a judge call saves both tokens and time.

**Stage 2** sends surviving pairs to an LLM judge that reads both answers side-by-side with randomized A/B ordering (seeded, so reproducible). The judge returns structured JSON: winner, optional confidence, reasons, citation assessments. Aggregate metrics are computed with bootstrap CIs, checked against configurable thresholds, and the process exits `0` (pass) or `2` (fail). `confidence` is advisory metadata and is not used for gate decisions.

## Features

- **Hard checks before judging** — Seven deterministic checks catch format violations without burning judge tokens. If it can be verified with code, it is.
- **Statistical rigor** — Win rate with 95% bootstrap confidence intervals. A number and a CI, not "A looks better."
- **Position bias mitigation** — A/B order is randomized per case with a seeded RNG. Optional two-pass judging re-evaluates `uncertain` verdicts with swapped order.
- **CI gating** — Configurable thresholds on win rate, CI lower bound, refusal rate, format compliance. Exit code 2 blocks the merge.
- **Judge calibration** — Dedicated pipeline measuring agreement, flip rate, and order bias against gold labels. Validates the judge before you trust it.
- **Metamorphic testing** — Shuffle context order, remove key chunks, paraphrase questions, inject distractors — then verify the model still produces citations and refuses correctly. Tests robustness, not just accuracy.
- **Full artifact trail** — Every run saves config snapshot, per-case outputs, hard checks, judge votes, and summary (JSON + Markdown) in a timestamped, git-SHA-tagged directory.

## When to Use This (and When Not To)

**Use this** if you're comparing two specific model/prompt/config variants on a fixed task, need a CI-gatable answer, and want to keep data and judge calls on your own infrastructure. It's built around citation-grounded QA but the architecture — dataset, hard checks, judge rubric, gates — generalizes to any task where you can define deterministic checks and a comparison rubric.

**Don't use this** if you need a hosted observability dashboard ([Langfuse](https://langfuse.com/), [Braintrust](https://braintrust.dev/)), want standardized multi-model benchmarks ([lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness), [OpenAI Evals](https://github.com/openai/evals)), or need real-time production traffic monitoring. This is a batch evaluation tool that runs in CI. It produces files, not a web UI.

## Configuration Example

```yaml
# Full evaluation with oracle context building and CI gates
run_name: regression_oracle
dataset_path: data/regression.jsonl

candidates:
  A:
    provider: openai                        # OpenAI API
    model: gpt-4o-mini
    system_prompt_path: system_prompts/candidate.txt
  B:
    provider: openai                        # Any OpenAI-compatible server works
    model: llama3.1:8b
    base_url: http://localhost:8080/v1      # llama.cpp, Ollama, vLLM, etc.
    system_prompt_path: system_prompts/candidate.txt

context_builder:
  mode: oracle_from_corpus                  # Build context from corpus/ directory
  corpus_root: corpus
  max_chars_per_chunk: 4000

task_contract:
  canonical_idk: "I don't know based on the provided context."
  require_citations_when: ["answer_with_citations"]
  citation_regex: '\[[A-Za-z0-9_-]+(?:\s+p|_p)\d+\]'

judge:
  enabled: true
  provider: openai
  model: gpt-4o-mini
  rubric_path: rubrics/judge_prompt.txt
  order_randomization_seed: 1337            # Deterministic A/B swap per case
  two_pass_on_uncertain: true               # Re-judge uncertain verdicts

gates:
  enabled: true
  win_rate_min: 0.50                        # A must win at least half
  win_rate_ci_lower_min: 0.40               # CI lower bound >= 40%
  refusal_rate_max: 0.20                    # Max 20% refusal per candidate
  format_pass_rate_min: 0.90                # 90%+ must pass hard checks

reproducibility:
  seed: 1337
```

## Project Status

- **Stable:** Core pipeline (run → hard checks → judge → metrics → gates), artifact generation, GitHub Actions CI, mock providers for zero-cost smoke testing.
- **Stable:** Judge calibration with agreement, flip rate, and order bias metrics against gold labels.
- **Experimental:** Metamorphic testing — transforms and invariants work but currently use mock providers only.
- **Out of scope:** Multi-model leaderboards, hosted dashboards, real-time monitoring, non-QA task types in v1.

## Repo Layout

```
eval_harness/               Core package
  ├── run.py                Main evaluation pipeline
  ├── calibrate.py          Judge calibration runner
  ├── replay.py             Failure replay
  ├── providers/            OpenAI, mock, mock judge
  ├── hard_checks/          7 deterministic checks
  ├── judge/                LLM judge + prompt builder
  ├── metamorphic/          Transforms + invariants
  ├── context_builder/      Oracle context from corpus
  ├── artifacts/            Artifact writer + metrics
  └── utils/                Logging, seeding, system prompts
tests/                      pytest suites
data/                       JSONL datasets (smoke: 40, regression: 425 cases)
corpus/                     Source documents for context building
configs/                    YAML run configurations
rubrics/                    Judge rubric
system_prompts/             System prompts for candidates and judge
```

**Contributing:** From a local source checkout, run `make test` and `make smoke-mock` before opening a PR. CI runs both automatically. The Makefile is not part of a `pip install`; installed users should use the `eval-harness` CLI. See [HOW_TO_RUN.md](HOW_TO_RUN.md) for detailed setup, artifact schemas, troubleshooting, and production workflows.

## Release Dry Run (TestPyPI)

Before publishing to production PyPI:

1. Bump `project.version` in `pyproject.toml`.
2. Run CI locally (`make test`, smoke, `python -m build`, `python -m twine check dist/*`).
3. Trigger the `Release-TestPyPI` GitHub Actions workflow with the same version string.
4. Verify package install from TestPyPI in a clean venv.
5. Trigger `Release` only after TestPyPI publish/install passes.

**License:** MIT
