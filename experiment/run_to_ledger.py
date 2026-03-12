"""Convert raw run data into the fixed energy ledger schema."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import cast

from experiment.energy_ledger import compute_stored_energy, integrate_power


def _as_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return cast(Mapping[str, object], value)


def _as_float(value: object, name: str) -> float:
    if isinstance(value, bool) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(cast(int | float, value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _as_trace_iterable(value: object) -> Iterable[object]:
    if isinstance(value, (str, bytes)):
        raise ValueError("run_data['resistor_traces'] must be iterable")
    try:
        iterable = cast(Iterable[object], value)
        iterator = iter(iterable)
    except TypeError as exc:
        raise ValueError("run_data['resistor_traces'] must be iterable") from exc
    return iterator


def build_ledger(run_data: object) -> dict[str, float]:
    data = _as_mapping(run_data, "run_data")
    required = (
        "driver_trace",
        "load_trace",
        "resistor_traces",
        "E_rad",
        "E_parasitic",
        "state_t0",
        "state_t1",
    )
    for key in required:
        if key not in data:
            raise ValueError(f"run_data missing key: {key}")

    e_driver = integrate_power(data["driver_trace"])
    e_load = integrate_power(data["load_trace"])

    e_r = 0.0
    for trace in _as_trace_iterable(data["resistor_traces"]):
        e_r += integrate_power(trace)

    e_stored_t0 = compute_stored_energy(data["state_t0"])
    e_stored_t1 = compute_stored_energy(data["state_t1"])

    return {
        "E_driver": e_driver,
        "E_load": e_load,
        "E_R": e_r,
        "E_rad": _as_float(data["E_rad"], "run_data['E_rad']"),
        "E_parasitic": _as_float(data["E_parasitic"], "run_data['E_parasitic']"),
        "E_stored_t0": e_stored_t0,
        "E_stored_t1": e_stored_t1,
    }
