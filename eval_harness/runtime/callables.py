"""Callable loading and response normalization utilities."""
from importlib import import_module
from typing import Any, Callable, Dict

from ..models import ModelResponse


def load_callable_from_string(spec: str) -> Callable[..., Any]:
    """Load a callable from module:function string."""
    if ":" not in spec:
        raise ValueError(
            f"Invalid callable path '{spec}'. Expected format 'module.submodule:function_name'"
        )

    module_path, function_name = spec.split(":", 1)
    if not module_path or not function_name:
        raise ValueError(
            f"Invalid callable path '{spec}'. Expected format 'module.submodule:function_name'"
        )

    module = import_module(module_path)
    fn = getattr(module, function_name, None)
    if fn is None or not callable(fn):
        raise ValueError(f"Callable '{function_name}' not found or not callable in module '{module_path}'")

    return fn


def normalize_model_response(raw: Any) -> ModelResponse:
    """Normalize external callable output into canonical internal ModelResponse."""
    if isinstance(raw, str):
        return ModelResponse(output=raw)

    if not isinstance(raw, dict):
        raise ValueError(
            f"Model callable must return str or dict with required 'output'. Got: {type(raw).__name__}"
        )

    if "output" not in raw:
        raise ValueError("Model callable dict response missing required key 'output'")

    output = raw["output"]
    if not isinstance(output, str):
        raise ValueError("Model callable response 'output' must be a string")

    metadata = raw.get("metadata")
    if metadata is None:
        metadata = {}
    elif not isinstance(metadata, dict):
        raise ValueError("Model callable response 'metadata' must be a dict when provided")

    return ModelResponse(
        output=output,
        citations=raw.get("citations"),
        latency_ms=raw.get("latency_ms"),
        token_usage=raw.get("token_usage"),
        model_id=raw.get("model_id"),
        metadata=metadata,
    )


def normalize_judge_response(raw: Any) -> Dict[str, Any]:
    """Normalize judge callable output to required structured response schema."""
    if not isinstance(raw, dict):
        raise ValueError(
            f"Judge callable must return dict with required 'winner'. Got: {type(raw).__name__}"
        )

    winner = raw.get("winner")
    valid_winners = {"A", "B", "tie", "uncertain"}
    if winner not in valid_winners:
        raise ValueError(
            "Judge callable response must include 'winner' with one of: "
            f"{sorted(valid_winners)}"
        )

    normalized = {
        "winner": winner,
        "reasons": raw.get("reasons", []),
        "citations_assessed": raw.get("citations_assessed", []),
        "notes": raw.get("notes", ""),
        "raw_response": raw.get("raw_response", ""),
    }

    if "confidence" in raw:
        normalized["confidence"] = raw["confidence"]

    return normalized
