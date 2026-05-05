# How to Run - Eval Harness (Complete Beginner's Guide)

This guide will walk you through running the evaluation harness from scratch, even if you're completely new to Python or command-line tools.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Quick Start (5 Minutes)](#quick-start-5-minutes)
4. [Understanding the Basics](#understanding-the-basics)
5. [Running Different Evaluations](#running-different-evaluations)
6. [Understanding the Results](#understanding-the-results)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you start, make sure you have:

1. **Python 3.10 or higher** installed
   - Check your version: Open a terminal and type `python --version`
   - If you don't have Python, download it from [python.org](https://www.python.org/downloads/)

2. **Git** (optional, for cloning the repo)
   - Check: `git --version`
   - Download from [git-scm.com](https://git-scm.com/)

3. **A text editor** (VS Code, Notepad++, or any editor you like)

---

## Installation

### Step 1: Navigate to the project directory

```bash
# If you already have the project, navigate to it
cd path/to/LLM-Evaluation-Harness

# Or if you're cloning it for the first time
git clone <repository-url>
cd LLM-Evaluation-Harness
```

### Step 2: Install dependencies

**Option A: Using Make (Recommended)**
```bash
make setup
```

**Option B: Manual installation**
```bash
# Create a virtual environment (optional but recommended)
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install the package with development tools
pip install .[dev]
```

### Step 3: Set up environment variables (optional for mock runs)

Create a `.env` file in the project root:

```bash
# Optional: Only needed if you want to use real models
OPENAI_API_KEY=your_openai_key_here

# For model A (OpenAI)
MODEL_A_PROVIDER=openai
MODEL_A_MODEL=gpt-4o-mini

# For model B (can be Ollama or another provider)
MODEL_B_PROVIDER=ollama
MODEL_B_MODEL=llama3.2:3b
MODEL_B_BASE_URL=http://localhost:11434/v1
MODEL_B_API_KEY=ollama

# Judge model
JUDGE_PROVIDER=openai
JUDGE_MODEL=gpt-4o-mini
```

**Note:** You can skip this step if you just want to run mock tests (no API costs).

---

## Quick Start (5 Minutes)

Let's run your first evaluation without any API costs!

### Run the smoke test with mock providers

```bash
make smoke-mock
```

**What this does:**
- Runs 40 test cases from `data/smoke.jsonl`
- Uses mock (fake) models so no API calls are made
- Takes about 5-10 seconds
- Creates a results folder in `artifacts/`

**Expected output:**
```
2026-01-19 15:00:00 - INFO - Loading config from configs/smoke_mock.yaml
2026-01-19 15:00:00 - INFO - Loaded 40 cases
2026-01-19 15:00:00 - INFO - Processing cases...
[1/40] Processing case cite_001
  Generating output from candidate A
  Generating output from candidate B
  Running judge...
  Judge verdict: tie (confidence: 0.00)
...
2026-01-19 15:00:10 - INFO - Evaluation complete! Artifacts written to artifacts/smoke_mock_20260119_150000
2026-01-19 15:00:10 - INFO - Summary: 40 cases, 30 judged
2026-01-19 15:00:10 - INFO - Gates disabled, skipping gate evaluation
```

**Check your results:**
```bash
# View the human-readable summary
cat artifacts/smoke_mock_*/summary.md

# Or open it in your editor
code artifacts/smoke_mock_*/summary.md
```

🎉 **Congratulations!** You just ran your first evaluation!

---

## Understanding the Basics

### What is this tool?

This is an **A/B regression gate** for comparing two AI models, prompts, or configurations before a change merges. It:

1. **Runs both models** on the same test cases
2. **Checks outputs** using deterministic rules (hard checks)
3. **Uses a judge** to compare subjective quality (only if both pass hard checks)
4. **Generates artifacts** with metrics, confidence intervals, and a CI-friendly exit code

### Key Concepts

**Candidates:**
- **Candidate A**: The first model/prompt you're testing
- **Candidate B**: The second model/prompt you're testing

**Hard Checks:**
- Deterministic rules (e.g., "output must have citations")
- Fast and objective
- Run before the judge

**Judge:**
- An LLM that compares A vs B subjectively
- Only runs if both candidates pass hard checks
- Can be mocked for testing

**Artifacts:**
- Results are saved in `artifacts/<run_id>/`
- Each run gets a unique folder with timestamp
- Contains all outputs, metrics, and reports

---

## Running Different Evaluations

### 1. Smoke Test with Mock Providers (No API costs)

**Use case:** Quick testing, CI/CD, development

```bash
make smoke-mock
```

**Time:** ~5-10 seconds
**Cost:** $0 (no API calls)
**Cases:** 40 test cases

---

### 2. Smoke Test with Real Models (Small cost)

**Use case:** Quick validation with real models

```bash
make smoke
```

**Prerequisites:**
- Set up `.env` with API keys (see Installation Step 3)
- Make sure you have credits/access to the models

**Time:** ~2-5 minutes (depending on model speed)
**Cost:** ~$0.10-0.50 (depends on models used)
**Cases:** 40 test cases

---

### 3. Full Regression Test (Production evaluation)

**Use case:** Complete evaluation with all features

```bash
make regression
# or
make eval
```

**Prerequisites:**
- `.env` configured with API keys
- Corpus files in `corpus/` directory (if using oracle mode)

**Time:** ~10-30 minutes (depends on dataset size)
**Cost:** Varies by dataset and models
**Features:**
- Uses `data/regression.jsonl` dataset
- Oracle context building from corpus
- Full gate evaluation with thresholds
- Confidence intervals

---

### 4. Judge Calibration (Check judge reliability)

**Use case:** Verify your judge is working correctly

```bash
make judge-healthcheck
```

**What it does:**
- Runs the judge on known test cases
- Measures agreement, flip rate, order bias
- Checks against configured thresholds
- **Exits with error if judge is unreliable**

**Expected output:**
```
============================================================
CALIBRATION RESULTS
============================================================
Agreement: 85.0%
Flip Rate: 10.0%
Order Bias: 5.0%

✓ PASS: min_agreement_pct
✓ PASS: max_flip_rate_pct
✓ PASS: max_order_bias_pct
============================================================
All thresholds passed!
```

---

### 5. Metamorphic Testing (Robustness check)

**Use case:** Test if your models are robust to input variations

```bash
make metamorphic
```

**What it does:**
- Applies transformations to inputs (paraphrase, reorder context, etc.)
- Checks if outputs maintain expected properties (invariants)
- Measures robustness score

**Expected output:**
```
============================================================
Metamorphic Testing Complete!
Robustness Score: 92.5%
============================================================
```

---

### 6. Replay a Specific Failure

**Use case:** Debug a specific test case that failed

```bash
make replay CASE_ID=cite_001 ARTIFACT_DIR=artifacts/smoke_mock_20260119_150000
```

**What it does:**
- Re-runs a single case with the exact same config
- Shows you the outputs and hard check results
- Compares with original run

---

## Understanding the Results

After any run, you'll find results in `artifacts/<run_id>/`. Let's understand each file:

### Artifact Files

```
artifacts/smoke_mock_20260119_150000/
├── config.yaml              # Exact config used for this run
├── run_meta.json            # Metadata (seed, timestamp, etc.)
├── cases.jsonl              # Test cases that were evaluated
├── outputs.jsonl            # Model outputs (A and B)
├── hard_checks.jsonl        # Hard check results (one line per case+candidate)
├── judge_votes.jsonl        # Judge decisions (only judged cases)
├── summary.json             # Summary statistics (machine-readable)
└── summary.md               # Human-readable summary (START HERE!)
```

### Reading summary.md

**Always start with `summary.md`** - it's designed to be human-readable.

#### Section 1: Metrics

```markdown
## Metrics

- **Win Rate (A):** 0.500
  - **95% CI:** [0.350, 0.650]
- **Refusal Rate (A):** 0.025
- **Refusal Rate (B):** 0.050
- **Format Pass Rate (A):** 0.950
- **Format Pass Rate (B):** 0.925
```

**What this means:**
- **Win Rate**: Candidate A won 50% of comparisons (ties count as 0.5 each)
- **95% CI**: We're 95% confident the true win rate is between 35% and 65%
- **Refusal Rate**: How often the model refused to answer (lower is better)
- **Format Pass Rate**: How often outputs passed hard checks (higher is better)

#### Section 2: Hard Check Results

```markdown
## Hard Check Results

- **Candidate A Failures:** 2/40
- **Candidate B Failures:** 3/40
```

**What this means:**
- Candidate A failed hard checks on 2 out of 40 cases
- Candidate B failed on 3 out of 40 cases

#### Section 3: Judge Results

```markdown
## Judge Results

- **Total Judged:** 35
- **A Wins:** 18
- **B Wins:** 15
- **Ties:** 2
- **Uncertain:** 0
- **Average Confidence:** 0.87
```

**What this means:**
- 35 cases were judged (5 were skipped due to hard check failures)
- A won 18 times, B won 15 times, 2 were ties
- Average judge confidence was 87%

#### Section 4: Per-Tag Breakdown

Shows results grouped by tags (e.g., chapter_1, citation_qa, etc.)

#### Section 5: Top Failures

Lists the top 3 failing cases with reasons - **very useful for debugging!**

#### Section 6: Budget Statistics

Shows latency and token usage - **useful for cost/performance optimization**

#### Section 7: Gate Result (if enabled)

```markdown
## Gate Result: PASS
```

or

```markdown
## Gate Result: FAIL

### Failures

- win_rate 0.450 < threshold 0.50
- format_pass_rate_a 0.850 < threshold 0.90
```

**What this means:**
- If PASS: Your evaluation met all quality thresholds
- If FAIL: Lists which thresholds were not met
- **Exit code**: 0 for PASS, 2 for FAIL (important for CI/CD)

---

## Advanced Features

### 1. Configuring Gates (Quality Thresholds)

Edit your config file (e.g., `configs/regression.yaml`):

```yaml
gates:
  enabled: true
  win_rate_min: 0.50              # A must win at least 50%
  win_rate_ci_lower_min: 0.40     # Lower bound of CI must be >= 40%
  refusal_rate_max: 0.20          # Max 20% refusal rate
  format_pass_rate_min: 0.90      # At least 90% must pass hard checks
  bootstrap_samples: 1000         # Number of bootstrap resamples
  confidence_level: 0.95          # 95% confidence interval
```

**When to use gates:**
- CI/CD pipelines (block merges if quality drops)
- Production deployments (ensure minimum quality)
- A/B testing (decide if B is actually better)

### 2. Regression Detection

Compare against a baseline:

```yaml
regression:
  enabled: true
  baseline_summary_path: artifacts/baseline_run/summary.json
  win_rate_drop_tolerance: 0.10   # Fail if win rate drops >10%
```

**Workflow:**
1. Run a baseline evaluation and save it
2. Point `baseline_summary_path` to that run's `summary.json`
3. Future runs will compare against the baseline

### 3. Custom Hard Checks

Add optional hard checks to your config:

```yaml
hard_checks:
  enabled: true
  fail_fast_per_candidate: true

  # Optional: Maximum length check
  max_length:
    max_chars: 3000

  # Optional: Forbidden phrases
  forbidden_phrases:
    phrases:
      - "As an AI language model"
      - "system prompt"
    case_insensitive: true

  # Optional: Latency budget
  latency_budget:
    max_latency_ms: 10000

  # Optional: Cost proxy (token estimation)
  cost_proxy:
    max_tokens: 2000
    chars_per_token: 4
```

### 4. Running Unit Tests

Before making changes, always run tests:

```bash
make test
```

**Expected output:**
```
============================= test session starts ==============================
...
tests/test_metrics.py::test_calculate_win_rate_basic PASSED
tests/test_metrics.py::test_bootstrap_ci_basic PASSED
...
============================== 31 passed in 0.50s ===============================
```

---

## Troubleshooting

### Problem: "ImportError: cannot import name..."

**Solution:**
```bash
# Reinstall dependencies
make setup

# Or manually
pip install --force-reinstall .[dev]
```

### Problem: "OPENAI_API_KEY not set"

**Solution:**
- Either create a `.env` file with your API key
- OR run mock tests instead: `make smoke-mock`

### Problem: "Judge healthcheck failed"

**Possible causes:**
1. Judge rubric is unclear
2. Test cases have wrong expected winners
3. Thresholds are too strict

**Solution:**
```bash
# Check the calibration report
cat artifacts/judge_calibration_*/reliability.md

# Adjust thresholds in configs/judge_calibration.yaml if needed
```

### Problem: "Gate result: FAIL"

**This is expected behavior!** Gates are designed to catch quality issues.

**What to do:**
1. Read the failure reasons in `summary.md`
2. Decide if you need to:
   - Fix the model/prompt (if quality truly dropped)
   - Adjust thresholds (if they're too strict)
   - Investigate specific failing cases

### Problem: Tests are slow

**Solutions:**
- Use `make smoke-mock` instead of `make smoke` (no API calls)
- Reduce dataset size for development
- Use faster models for quick iterations

### Problem: Can't find artifacts

**Solution:**
```bash
# List all artifact directories
ls -la artifacts/

# Find the most recent one
ls -t artifacts/ | head -1

# View summary
cat artifacts/$(ls -t artifacts/ | head -1)/summary.md
```

---

## Common Workflows

### Workflow 1: Development Cycle

```bash
# 1. Make code changes
vim eval_harness/some_file.py

# 2. Run unit tests
make test

# 3. Run quick smoke test
make smoke-mock

# 4. Check results
cat artifacts/smoke_mock_*/summary.md

# 5. If good, commit and push
git add .
git commit -m "Your changes"
git push
```

### Workflow 2: Before Production Deployment

```bash
# 1. Run full regression test
make eval

# 2. Run judge healthcheck
make judge-healthcheck

# 3. Run metamorphic tests
make metamorphic

# 4. Review all artifacts
cat artifacts/regression_*/summary.md
cat artifacts/judge_calibration_*/reliability.md
cat artifacts/metamorphic_*/metamorphic_summary.md

# 5. If all pass, deploy
```

### Workflow 3: Debugging a Failure

```bash
# 1. Find the failing case ID in summary.md
cat artifacts/your_run/summary.md
# Look at "Top Failures" section

# 2. Replay the specific case
make replay CASE_ID=cite_001 ARTIFACT_DIR=artifacts/your_run

# 3. Inspect outputs
cat artifacts/your_run/outputs.jsonl | grep cite_001
cat artifacts/your_run/hard_checks.jsonl | grep cite_001

# 4. Fix the issue
# 5. Re-run the evaluation
```

---

## Next Steps

Now that you know how to run evaluations:

1. **Read the docs:**
   - `README.md` - Overview and quickstart
   - `PROJECT.md` - v1 product scope and contracts
   - `changes.md` - Summary of the recent PyPI/callable updates
   - `artifacts/artifacts_spec.md` - Artifact schema reference

2. **Try different configs:**
   - Edit `configs/smoke_mock.yaml`
   - Add your own test cases to `data/smoke.jsonl`
   - Experiment with different hard checks

3. **Integrate with CI/CD:**
   - See `.github/workflows/ci.yml` for GitHub Actions example
   - Use `make smoke-mock` in your pipeline
   - Gates will automatically fail builds on quality regressions

4. **Get help:**
   - Check troubleshooting section above
   - Review error messages carefully
   - Open an issue if you find bugs

---

## Summary of Commands

```bash
# Setup
make setup                    # Install dependencies

# Testing
make test                     # Run unit tests

# Evaluations
make smoke-mock              # Quick test (no API costs)
make smoke                   # Quick test (real models)
make eval                    # Full evaluation
make regression              # Same as eval

# Advanced
make judge-healthcheck       # Check judge reliability
make metamorphic             # Robustness testing
make replay CASE_ID=... ARTIFACT_DIR=...  # Debug specific case
```

---

**Happy evaluating!** 🚀

If you have questions or run into issues, refer to the troubleshooting section or check the project documentation.
