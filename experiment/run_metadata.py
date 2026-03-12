"""Normalize experimental run metadata for traceable evidence records."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import cast


_METADATA_KEYS = (
    "device_ids",
    "operator",
    "timestamp",
    "calibration_ids",
    "ambient_conditions",
    "sample_rates",
    "comments",
)


def _as_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return cast(Mapping[str, object], value)


def _as_text(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _as_float(value: object, name: str) -> float:
    if isinstance(value, bool) or isinstance(value, (bytes, bytearray)):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(cast(int | float | str, value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if number != number or number in (float("inf"), float("-inf")):
        raise ValueError(f"{name} must be finite")
    return number


def _normalize_text_map(value: object, name: str) -> dict[str, str]:
    data = _as_mapping(value, name)
    if not data:
        raise ValueError(f"{name} must not be empty")

    normalized: dict[str, str] = {}
    for key, item in data.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"{name} keys must be non-empty strings")
        normalized[key.strip()] = _as_text(item, f"{name}['{key}']")
    return normalized


def _normalize_ambient_conditions(value: object, name: str) -> dict[str, float | str]:
    data = _as_mapping(value, name)
    if not data:
        raise ValueError(f"{name} must not be empty")

    normalized: dict[str, float | str] = {}
    for key, item in data.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"{name} keys must be non-empty strings")
        field_name = f"{name}['{key}']"
        if isinstance(item, str):
            text = _as_text(item, field_name)
            try:
                normalized[key.strip()] = _as_float(text, field_name)
            except ValueError:
                normalized[key.strip()] = text
        else:
            normalized[key.strip()] = _as_float(item, field_name)
    return normalized


def _normalize_sample_rates(value: object, name: str) -> dict[str, float]:
    data = _as_mapping(value, name)
    if not data:
        raise ValueError(f"{name} must not be empty")

    normalized: dict[str, float] = {}
    for key, item in data.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"{name} keys must be non-empty strings")
        rate = _as_float(item, f"{name}['{key}']")
        if rate <= 0.0:
            raise ValueError(f"{name}['{key}'] must be > 0")
        normalized[key.strip()] = rate
    return normalized


def _normalize_timestamp(value: object, name: str) -> str:
    text = _as_text(value, name)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        timestamp = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{name} must be ISO-8601") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"{name} must include timezone information")
    return timestamp.isoformat()


def normalize_run_metadata(metadata: object) -> dict[str, object]:
    """Validate and normalize the locked metadata schema for a run."""
    data = _as_mapping(metadata, "metadata")
    if set(data.keys()) != set(_METADATA_KEYS):
        raise ValueError("metadata must contain the locked run metadata schema")

    comments = data["comments"]
    if not isinstance(comments, str):
        raise ValueError("metadata['comments'] must be a string")

    return {
        "device_ids": _normalize_text_map(data["device_ids"], "metadata['device_ids']"),
        "operator": _as_text(data["operator"], "metadata['operator']"),
        "timestamp": _normalize_timestamp(data["timestamp"], "metadata['timestamp']"),
        "calibration_ids": _normalize_text_map(data["calibration_ids"], "metadata['calibration_ids']"),
        "ambient_conditions": _normalize_ambient_conditions(
            data["ambient_conditions"],
            "metadata['ambient_conditions']",
        ),
        "sample_rates": _normalize_sample_rates(data["sample_rates"], "metadata['sample_rates']"),
        "comments": comments.strip(),
    }
