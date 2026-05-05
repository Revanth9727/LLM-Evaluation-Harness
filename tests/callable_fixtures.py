"""Callable fixtures for runtime integration tests."""

judge_call_count = 0


def candidate_a(*, input: str, context=None, metadata=None):
    return {
        "output": f"A says: {input} [DOC_p1]",
        "model_id": "candidate_a_v1",
        "metadata": {"path": "dict"},
    }


def candidate_b(*, input: str, context=None, metadata=None):
    return f"B says: {input} [DOC_p1]"


def candidate_raises(*, input: str, context=None, metadata=None):
    raise RuntimeError("candidate exploded")


def judge_uncertain_then_tie(*, prompt: str, metadata=None):
    global judge_call_count
    judge_call_count += 1
    if judge_call_count == 1:
        return {"winner": "uncertain", "notes": "first pass uncertain"}
    return {"winner": "tie", "confidence": 0.25, "notes": "second pass tie"}


def judge_raises(*, prompt: str, metadata=None):
    raise RuntimeError("judge exploded")


def reset_judge_counter():
    global judge_call_count
    judge_call_count = 0
