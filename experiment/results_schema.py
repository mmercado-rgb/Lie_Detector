"""Validate and normalize deterministic run results."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Literal, TypedDict, cast


_RESULT_KEYS = ("ledger", "residual", "label")
_LEDGER_KEYS = (
    "E_driver",
    "E_load",
    "E_R",
    "E_rad",
    "E_parasitic",
    "E_stored_t0",
    "E_stored_t1",
)
_VALID_LABELS = ("CLOSED", "UNDERACCOUNTED", "APPARENT_EXCESS")
ResultLabel = Literal["CLOSED", "UNDERACCOUNTED", "APPARENT_EXCESS"]


class ResultRecord(TypedDict):
    ledger: dict[str, float]
    residual: float
    label: ResultLabel


def _as_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return cast(Mapping[str, object], value)


def _as_float(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(cast(int | float | str, value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def make_result_record(result: object) -> ResultRecord:
    data = _as_mapping(result, "result")
    if set(data.keys()) != set(_RESULT_KEYS):
        raise ValueError("result must contain exactly ledger, residual, and label")

    ledger = _as_mapping(data["ledger"], "result['ledger']")
    if set(ledger.keys()) != set(_LEDGER_KEYS):
        raise ValueError("result['ledger'] must contain the locked ledger schema")

    label = data["label"]
    if not isinstance(label, str) or label not in _VALID_LABELS:
        raise ValueError("result['label'] must be a valid classification")

    return {
        "ledger": {
            key: _as_float(ledger[key], f"result['ledger']['{key}']")
            for key in _LEDGER_KEYS
        },
        "residual": _as_float(data["residual"], "result['residual']"),
        "label": cast(ResultLabel, label),
    }
