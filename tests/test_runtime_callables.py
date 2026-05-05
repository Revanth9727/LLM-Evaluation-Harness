"""Tests for callable runtime and config seams."""

import json

import pytest
import yaml

from eval_harness.config import validate_run_config
from eval_harness.judge.runner import JudgeRunner
from eval_harness.models import Case
from eval_harness.run import run_evaluation
from eval_harness.runtime.callables import (
    load_callable_from_string,
    normalize_judge_response,
    normalize_model_response,
)


def test_load_callable_from_string_happy_path():
    fn = load_callable_from_string("tests.callable_fixtures:candidate_a")
    result = fn(input="hello", context=None, metadata=None)
    assert isinstance(result, dict)
    assert result["output"] == "A says: hello [DOC_p1]"


def test_load_callable_from_string_rejects_bad_format():
    with pytest.raises(ValueError, match="Invalid callable path"):
        load_callable_from_string("tests.callable_fixtures.candidate_a")


def test_normalize_model_response_string_boundary():
    normalized = normalize_model_response("plain text")
    assert normalized.output == "plain text"
    assert normalized.metadata == {}


def test_normalize_model_response_dict_happy_path():
    normalized = normalize_model_response(
        {
            "output": "hello",
            "citations": ["DOC_p1"],
            "latency_ms": 12.3,
            "token_usage": {"total_tokens": 10},
            "model_id": "m1",
            "metadata": {"region": "us"},
        }
    )
    assert normalized.output == "hello"
    assert normalized.citations == ["DOC_p1"]
    assert normalized.latency_ms == 12.3
    assert normalized.token_usage == {"total_tokens": 10}
    assert normalized.model_id == "m1"
    assert normalized.metadata == {"region": "us"}


def test_normalize_model_response_dict_requires_output():
    with pytest.raises(ValueError, match="missing required key 'output'"):
        normalize_model_response({"foo": "bar"})


def test_normalize_judge_response_validates_winner():
    with pytest.raises(ValueError, match="must include 'winner'"):
        normalize_judge_response({"winner": "maybe"})


def _base_config():
    return {
        "run_name": "test",
        "dataset_path": "data/smoke.jsonl",
        "candidates": {
            "A": {"provider": "mock", "model": "mock_a"},
            "B": {"provider": "mock", "model": "mock_b"},
        },
    }


def test_validate_run_config_candidate_requires_provider_xor_callable():
    config = _base_config()
    config["candidates"]["A"] = {
        "provider": "mock",
        "model": "mock_a",
        "callable": "tests.callable_fixtures:candidate_a",
    }

    with pytest.raises(ValueError, match="exactly one of 'provider' or 'callable'"):
        validate_run_config(config)


def test_validate_run_config_accepts_callable_candidate():
    config = _base_config()
    config["candidates"]["A"] = {"callable": "tests.callable_fixtures:candidate_a"}
    validate_run_config(config)


def test_validate_run_config_rejects_enabled_judge_without_provider_or_callable():
    config = _base_config()
    config["judge"] = {"enabled": True, "rubric_path": "rubrics/judge_prompt.txt"}

    with pytest.raises(ValueError, match="Judge must define exactly one of 'provider' or 'callable'"):
        validate_run_config(config)


def test_judge_runner_two_pass_uses_uncertain_state_not_confidence():
    from tests import callable_fixtures

    callable_fixtures.reset_judge_counter()
    judge_callable = load_callable_from_string("tests.callable_fixtures:judge_uncertain_then_tie")

    runner = JudgeRunner(
        {
            "enabled": True,
            "two_pass_on_uncertain": True,
            "order_randomization_seed": 7,
            "rubric_path": "rubrics/judge_prompt.txt",
        },
        judge_callable=judge_callable,
    )

    vote = runner.judge_case(
        Case(id="c1", input="What is AI?", expected_behavior="answer_with_citations", tags=[]),
        output_a="A output",
        output_b="B output",
    )

    assert vote is not None
    assert vote.winner == "tie"
    assert callable_fixtures.judge_call_count == 2


def test_judge_runner_callable_exception_returns_uncertain_vote():
    judge_callable = load_callable_from_string("tests.callable_fixtures:judge_raises")

    runner = JudgeRunner(
        {
            "enabled": True,
            "two_pass_on_uncertain": True,
            "order_randomization_seed": 7,
            "rubric_path": "rubrics/judge_prompt.txt",
        },
        judge_callable=judge_callable,
    )

    vote = runner.judge_case(
        Case(id="c1", input="What is AI?", expected_behavior="answer_with_citations", tags=[]),
        output_a="A output",
        output_b="B output",
    )

    assert vote is not None
    assert vote.winner == "uncertain"
    assert any("Judge error" in reason for reason in vote.reasons)


def test_run_evaluation_with_candidate_and_judge_callables(tmp_path):
    from tests import callable_fixtures

    callable_fixtures.reset_judge_counter()

    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text(
        json.dumps({"id": "c1", "input": "What is AI?", "expected_behavior": "answer_with_citations"}) + "\n",
        encoding="utf-8",
    )

    artifacts_root = tmp_path / "artifacts"
    config_path = tmp_path / "config.yaml"
    config = {
        "run_name": "callable_smoke",
        "dataset_path": str(dataset_path),
        "candidates": {
            "A": {"callable": "tests.callable_fixtures:candidate_a"},
            "B": {"callable": "tests.callable_fixtures:candidate_b"},
        },
        "judge": {
            "enabled": True,
            "callable": "tests.callable_fixtures:judge_uncertain_then_tie",
            "order_randomization_seed": 42,
            "two_pass_on_uncertain": True,
        },
        "gates": {"enabled": False},
        "artifacts": {"root_dir": str(artifacts_root)},
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    exit_code = run_evaluation(str(config_path))
    assert exit_code == 0
    assert callable_fixtures.judge_call_count == 2

    run_dirs = [p for p in artifacts_root.iterdir() if p.is_dir()]
    assert run_dirs, "Expected at least one artifact run directory"


def test_run_evaluation_callable_candidate_exception_written_to_artifacts(tmp_path):
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text(
        json.dumps({"id": "c1", "input": "What is AI?", "expected_behavior": "answer_with_citations"}) + "\n",
        encoding="utf-8",
    )

    artifacts_root = tmp_path / "artifacts"
    config_path = tmp_path / "config.yaml"
    config = {
        "run_name": "callable_error",
        "dataset_path": str(dataset_path),
        "candidates": {
            "A": {"callable": "tests.callable_fixtures:candidate_raises"},
            "B": {"callable": "tests.callable_fixtures:candidate_b"},
        },
        "judge": {"enabled": False},
        "gates": {"enabled": False},
        "artifacts": {"root_dir": str(artifacts_root)},
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    exit_code = run_evaluation(str(config_path))
    assert exit_code == 0

    run_dirs = [p for p in artifacts_root.iterdir() if p.is_dir()]
    assert run_dirs
    latest = sorted(run_dirs)[-1]
    outputs_path = latest / "outputs.jsonl"
    lines = [json.loads(line) for line in outputs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    assert "error_a" in lines[0]
    assert "candidate exploded" in lines[0]["error_a"]


def test_run_evaluation_provider_backward_compat_path(tmp_path):
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text(
        json.dumps({"id": "c1", "input": "What is AI?", "expected_behavior": "answer_with_citations"}) + "\n",
        encoding="utf-8",
    )

    artifacts_root = tmp_path / "artifacts"
    config_path = tmp_path / "config.yaml"
    config = {
        "run_name": "provider_smoke",
        "dataset_path": str(dataset_path),
        "candidates": {
            "A": {"provider": "mock", "model": "mock_a"},
            "B": {"provider": "mock", "model": "mock_b"},
        },
        "judge": {"enabled": False},
        "gates": {"enabled": False},
        "artifacts": {"root_dir": str(artifacts_root)},
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    exit_code = run_evaluation(str(config_path))
    assert exit_code == 0
    run_dirs = [p for p in artifacts_root.iterdir() if p.is_dir()]
    assert run_dirs
