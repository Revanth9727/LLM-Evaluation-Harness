# Artifacts Spec (Required Outputs Per Run)

Every eval run must write a self-contained artifact bundle under:

artifacts/<run_id>/

Where:
- run_id is unique (timestamp + short hash is fine)
- artifacts are sufficient to debug, compare A vs B, and replay the same inputs

---

## Required directory layout

artifacts/
  <run_id>/
    config.yaml
    run_meta.json
    cases.jsonl
    outputs.jsonl
    hard_checks.jsonl
    judge_votes.jsonl          (may be absent if judge disabled or skipped)
    summary.json
    summary.md

---

## File definitions (required)

### 1) config.yaml
Exact config used for the run (resolved after env var substitution if applicable).

### 2) run_meta.json
Run-level metadata, minimum fields:
- run_id
- run_name
- started_at (ISO-8601)
- finished_at (ISO-8601)
- git_commit (optional)
- dataset_path
- candidate_models:
    A: {provider, model}
    B: {provider, model}
- judge_model (optional)
- context_mode: smoke | oracle_from_corpus | rag
- corpus_root (if used)
- page_offset (if used)

### 3) cases.jsonl
One line per case, minimum fields:
- id
- input (normalized; `question` should be mapped to `input`)
- expected_behavior
- tags
- sources (as provided)
- context (the exact context passed to models A and B)
- context_build:
    mode
    dataset_pages: [..]
    corpus_pages: [..]
    truncation: true/false

### 4) outputs.jsonl
One line per case, minimum fields:
- id
- answer_a
- answer_b
- model_a_info: {provider, model}
- model_b_info: {provider, model}

### 5) hard_checks.jsonl
One line per case, minimum fields:
- id
- candidate: "A" | "B"
- passed: true/false
- checks: list of:
    {name, passed, severity, reason, details}

Also include:
- skip_judge: true/false
- skip_reason: string (if skipped)

Hard check failures MUST cause skip_judge=true for that case.

### 6) judge_votes.jsonl (optional per case, but file should exist if judge enabled)
One line per case that was judged:
- id
- winner: "A" | "B" | "tie" | "uncertain"
- confidence: 0.0 - 1.0
- reasons: [..]
- order: "A_then_B" | "B_then_A"
- raw_response: string (the judge model raw text output)

No entry should exist for cases where judge was skipped.

### 7) summary.json
Run-level stats, minimum fields:
- run_id
- total_cases
- hard_check_pass_rate:
    A: float
    B: float
- judged_cases
- wins:
    A: int
    B: int
    tie: int
    uncertain: int
- skips_due_to_hard_checks: int
- failures_by_check_name:
    <check_name>: count

### 8) summary.md
Human-readable summary including:
- run name + timestamp
- models A/B (+ judge if enabled)
- total cases
- hard check pass rates and top failing checks
- judged cases + win/tie counts
- list of the worst failures (top 10 case IDs) with reasons and pointers to artifact lines

---

## Naming conventions (required)
- Citations in context chunk headers must be: [DOC_ID pDATASET_PAGE]
- If a page_offset is used, it must be recorded in run_meta.json and cases.jsonl

---

## Determinism expectations
- If context is built from corpus, cases.jsonl must record corpus pages used.
- If truncation occurs, record it and keep it deterministic.

---

## Non-goals
- No UI dashboards required.
- No database required.
- Artifacts must remain plain files committed nowhere (generated outputs only).
