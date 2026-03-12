"""Compare the electrical ledger against independent measurement estimates."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import cast

from experiment.energy_ledger import compute_residual


def _as_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return cast(Mapping[str, object], value)


def _as_float(value: object, name: str) -> float:
    if isinstance(value, bool) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(cast(int | float, value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _normalize_ledger(ledger: object) -> dict[str, float]:
    data = _as_mapping(ledger, "ledger")
    required = (
        "E_driver",
        "E_load",
        "E_R",
        "E_rad",
        "E_parasitic",
        "E_stored_t0",
        "E_stored_t1",
    )
    if set(data.keys()) != set(required):
        raise ValueError("ledger must contain the locked ledger schema")
    return {
        key: _as_float(data[key], f"ledger['{key}']")
        for key in required
    }


def _normalize_battery_depletion(data: object) -> dict[str, float]:
    record = _as_mapping(data, "cross_checks['battery_depletion']")
    if set(record.keys()) != {"observed_input_energy", "tolerance"}:
        raise ValueError("cross_checks['battery_depletion'] must contain observed_input_energy and tolerance")
    tolerance = _as_float(record["tolerance"], "cross_checks['battery_depletion']['tolerance']")
    if tolerance < 0.0:
        raise ValueError("cross_checks['battery_depletion']['tolerance'] must be >= 0")
    return {
        "observed_input_energy": _as_float(
            record["observed_input_energy"],
            "cross_checks['battery_depletion']['observed_input_energy']",
        ),
        "tolerance": tolerance,
    }


def _normalize_calorimetry(data: object) -> dict[str, float]:
    record = _as_mapping(data, "cross_checks['calorimetry']")
    if set(record.keys()) != {"observed_output_energy", "tolerance"}:
        raise ValueError("cross_checks['calorimetry'] must contain observed_output_energy and tolerance")
    tolerance = _as_float(record["tolerance"], "cross_checks['calorimetry']['tolerance']")
    if tolerance < 0.0:
        raise ValueError("cross_checks['calorimetry']['tolerance'] must be >= 0")
    return {
        "observed_output_energy": _as_float(
            record["observed_output_energy"],
            "cross_checks['calorimetry']['observed_output_energy']",
        ),
        "tolerance": tolerance,
    }


def evaluate_cross_checks(ledger: object, cross_checks: object | None) -> dict[str, object]:
    """Return pass/fail comparisons for any supplied independent estimates."""
    normalized_ledger = _normalize_ledger(ledger)
    if cross_checks is None:
        return {
            "status": "NOT_AVAILABLE",
            "passed": True,
            "comparisons": {},
            "reasons": [],
        }

    data = _as_mapping(cross_checks, "cross_checks")
    allowed_keys = {"battery_depletion", "calorimetry"}
    if set(data.keys()) - allowed_keys:
        raise ValueError("cross_checks contains unknown keys")

    comparisons: dict[str, dict[str, float | bool]] = {}
    reasons: list[str] = []
    residual = compute_residual(normalized_ledger)
    electrical_output = normalized_ledger["E_driver"] - residual

    if "battery_depletion" in data:
        battery = _normalize_battery_depletion(data["battery_depletion"])
        difference = battery["observed_input_energy"] - normalized_ledger["E_driver"]
        passed = abs(difference) <= battery["tolerance"]
        comparisons["battery_depletion"] = {
            "reference_energy": normalized_ledger["E_driver"],
            "observed_energy": battery["observed_input_energy"],
            "difference": difference,
            "tolerance": battery["tolerance"],
            "passed": passed,
        }
        if not passed:
            reasons.append("battery depletion disagrees with electrical driver energy")

    if "calorimetry" in data:
        calorimetry = _normalize_calorimetry(data["calorimetry"])
        difference = calorimetry["observed_output_energy"] - electrical_output
        passed = abs(difference) <= calorimetry["tolerance"]
        comparisons["calorimetry"] = {
            "reference_energy": electrical_output,
            "observed_energy": calorimetry["observed_output_energy"],
            "difference": difference,
            "tolerance": calorimetry["tolerance"],
            "passed": passed,
        }
        if not passed:
            reasons.append("calorimetry disagrees with electrical ledger output")

    status = "NOT_AVAILABLE"
    if comparisons:
        status = "PASS" if not reasons else "FAIL"

    return {
        "status": status,
        "passed": not reasons,
        "comparisons": comparisons,
        "reasons": reasons,
    }
