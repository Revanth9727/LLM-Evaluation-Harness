# Project 1 - Eval Harness

A production-ready, CI-gated A/B evaluation framework for comparing AI models, prompts, or configurations with confidence intervals, quality gates, and comprehensive reporting.

## Key Features

✅ **Hard Checks First** - Deterministic validation (schema, citations, length, etc.)
✅ **LLM Judge** - Subjective quality comparison (only when hard checks pass)
✅ **Metrics + Confidence Intervals** - Win rate, refusal rate, format pass rate with bootstrap 95% CI
✅ **Quality Gates** - Configurable thresholds that fail builds on regressions
✅ **Judge Calibration** - Verify judge reliability with agreement, flip rate, order bias metrics
✅ **Metamorphic Testing** - Robustness checks via input transformations
✅ **Failure Replay** - Debug specific cases with exact reproduction
✅ **CI/CD Ready** - GitHub Actions integration with artifact uploads

## Quick Start (2 Minutes)

### 1. Install dependencies
```bash
make setup
```

### 2. Run your first evaluation (no API costs)
```bash
make smoke-mock
```

### 3. Check results
```bash
cat artifacts/smoke_mock_*/summary.md
```

🎉 **Done!** You just ran an A/B evaluation with 40 test cases.

## Core Capabilities

### Metrics with Statistical Rigor

Every run produces:
- **Win Rate** - How often Candidate A wins vs B (with 95% CI)
- **Refusal Rate** - How often each model refuses to answer
- **Format Pass Rate** - How often outputs meet requirements
- **Per-Tag Breakdown** - Metrics grouped by test categories
- **Budget Stats** - Latency and token usage tracking

### Quality Gates (CI/CD Integration)

```yaml
gates:
  enabled: true
  win_rate_min: 0.50              # Minimum win rate
  win_rate_ci_lower_min: 0.40     # Lower CI bound must be >= 40%
  refusal_rate_max: 0.20          # Max refusal rate
  format_pass_rate_min: 0.90      # Min format compliance
```

**Exit codes:**
- `0` = PASS (all gates met)
- `2` = FAIL (quality regression detected)

### Regression Detection

```yaml
regression:
  enabled: true
  baseline_summary_path: artifacts/baseline/summary.json
  win_rate_drop_tolerance: 0.10   # Fail if drop > 10%
```

## Common Commands

```bash
# Development & Testing
make test                        # Run unit tests (31 tests)
make smoke-mock                  # Quick test with mock models (no cost)
make smoke                       # Quick test with real models

# Production Evaluation
make eval                        # Full evaluation with all features
make regression                  # Same as eval (alias)

# Quality Assurance
make judge-healthcheck           # Verify judge reliability
make metamorphic                 # Test robustness to input variations

# Debugging
make replay CASE_ID=cite_001 ARTIFACT_DIR=artifacts/run_20260119
```

## Technology Stack

- **Python 3.10+** - Core language
- **pytest** - Testing framework (31 unit tests)
- **NumPy** - Statistical computations (bootstrap CI)
- **YAML** - Configuration format
- **JSONL** - Dataset format
- **Makefile** - Unified command interface
- **GitHub Actions** - CI/CD automation

**LLM Providers Supported:**
- OpenAI (GPT-4, GPT-4o, etc.)
- Ollama (local models)
- Any OpenAI-compatible API

## Documentation

### Start Here (New Users)
- **🚀 [HOW_TO_RUN.md](HOW_TO_RUN.md)** - Complete beginner's guide (start here!)
- **📘 [docs/project1_eval_harness.md](docs/project1_eval_harness.md)** - Full project explanation

### Specifications & Contracts
- **📋 [CLAUDE.md](CLAUDE.md)** - Project constitution (how AI should modify this repo)
- **📦 [docs/ARTIFACTS_SPEC.md](docs/ARTIFACTS_SPEC.md)** - Artifact schemas (source of truth)
- **✅ [docs/Project1_Complete_Checklist.md](docs/Project1_Complete_Checklist.md)** - Definition of Done
- **📝 [docs/task_contract.md](docs/task_contract.md)** - What "passing" means for Citation Q&A
- **🔒 [docs/hard_checks.md](docs/hard_checks.md)** - Deterministic validation rules
- **⚖️ [docs/judge_rubric.md](docs/judge_rubric.md)** - Judge comparison criteria

### Advanced Topics
- **📊 [docs/judge_calibration.md](docs/judge_calibration.md)** - Judge reliability methodology
- **🔄 [docs/metamorphic_testing.md](docs/metamorphic_testing.md)** - Robustness testing guide
- **🐛 [docs/runbook_interpreting_reports.md](docs/runbook_interpreting_reports.md)** - How to debug failures

> **💡 Tip:** If you're new, read [HOW_TO_RUN.md](HOW_TO_RUN.md) first. It has everything you need to get started!

## Repository layout

- `eval_harness/` - harness code (runner, providers, checks, judge)
- `tests/` - pytest test suites
- `data/` - datasets (JSONL)
- `corpus/` - source documents for oracle context building
- `rubrics/` - judge rubric + exemplars
- `system_prompts/` - system prompts for LLMs
- `configs/` - run configs (YAML)
- `artifacts/` - run outputs and reports
- `docs/` - project documentation
- `.github/workflows/` - CI/CD workflows

## Artifacts

Every run creates a timestamped folder: `artifacts/<run_name>_<timestamp>_<git_sha>/`

### Standard Evaluation Run (8 files)

1. **config.yaml** - Exact config snapshot used
2. **run_meta.json** - Metadata (seed, timestamp, total cases)
3. **cases.jsonl** - Test cases evaluated
4. **outputs.jsonl** - Model outputs (A and B, with latency)
5. **hard_checks.jsonl** - Hard check results (one line per case+candidate)
6. **judge_votes.jsonl** - Judge decisions (only for cases that passed hard checks)
7. **summary.json** - Complete metrics and statistics (machine-readable)
8. **summary.md** - Human-readable report (⭐ **start here!**)

### Example summary.json (with new metrics)

```json
{
  "run_name": "smoke_mock",
  "total_cases": 40,
  "metrics": {
    "win_rate": 0.500,
    "win_rate_ci": {"lower": 0.350, "upper": 0.650},
    "refusal_rate_a": 0.025,
    "refusal_rate_b": 0.050,
    "format_pass_rate_a": 0.950,
    "format_pass_rate_b": 0.925
  },
  "per_tag_breakdown": {
    "chapter_1": {"total_cases": 5, "a_hard_check_failures": 0, ...},
    ...
  },
  "budget_stats": {
    "latency_ms": {"candidate_a": {"avg": 234.5, "max": 450.2}, ...},
    ...
  },
  "gate_result": {
    "decision": "PASS",
    "failures": [],
    "warnings": []
  }
}
```

### Special Run Artifacts

**Judge Calibration:**
- `reliability.json` - Metrics (agreement, flip rate, order bias)
- `reliability.md` - Human-readable calibration report

**Metamorphic Testing:**
- `metamorphic_results.json` - Full transformation results
- `metamorphic_summary.md` - Robustness score breakdown
- `outputs_transformed.jsonl` - Transformed outputs

> See [docs/ARTIFACTS_SPEC.md](docs/ARTIFACTS_SPEC.md) for complete schemas

## Contributing

### Development Workflow

1. **Make changes** to code or test cases
2. **Run unit tests:** `make test` (must pass all 31 tests)
3. **Run smoke test:** `make smoke-mock` (quick validation, no API costs)
4. **Check results:** `cat artifacts/smoke_mock_*/summary.md`
5. **If judge/rubric changed:** `make judge-healthcheck` (verify reliability)
6. **Open PR:** CI automatically runs tests and smoke eval

### CI/CD Integration

The repo includes `.github/workflows/ci.yml` that runs on every PR:

```yaml
✅ Unit tests (pytest)
✅ Smoke test with mock providers
✅ Artifact uploads
✅ Gate evaluation (blocks merge on FAIL)
```

**No API keys needed for CI** - mock providers enable zero-cost testing.

### Before Production Deployment

Run the full validation suite:

```bash
make test                    # Unit tests
make eval                    # Full evaluation
make judge-healthcheck       # Judge reliability
make metamorphic             # Robustness testing
```

All should pass before deploying changes.

## What's New in This Version

### Recent Updates (January 2026)

✨ **New Metrics:**
- Win rate with 95% bootstrap confidence intervals
- Per-candidate refusal rates
- Format pass rates
- Per-tag breakdown in all reports

✨ **Quality Gates:**
- Configurable thresholds (win_rate, refusal_rate, format_pass_rate)
- Regression detection vs baseline
- Exit code 2 on FAIL (blocks CI/CD)

✨ **Enhanced Reporting:**
- Budget statistics (latency, tokens)
- Top 3 failure examples
- Gate results in summary

✨ **Improved Replay:**
- `make replay` now executes (previously just printed usage)
- Pass CASE_ID and ARTIFACT_DIR as arguments

See [docs/Project1_fixes.md](docs/Project1_fixes.md) for implementation details.

## Support & Troubleshooting

- **📖 Read [HOW_TO_RUN.md](HOW_TO_RUN.md)** - Comprehensive troubleshooting guide
- **🔍 Check error messages** - They're designed to be helpful
- **🐛 Review artifacts** - `summary.md` shows what went wrong
- **💬 Open an issue** - We're here to help!

## License

Internal project. See your organization's licensing terms.
