"""Deterministic energy ledger calculations."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import cast


def _as_float(value: object, name: str) -> float:
    """Convert a validated numeric input to float."""
    if isinstance(value, bool) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(cast(int | float, value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _as_float_list(value: object, name: str) -> list[float]:
    """Convert a validated non-string iterable to a float list."""
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be a non-string iterable")
    try:
        iterable = cast(Iterable[object], value)
        items = iter(iterable)
    except TypeError as exc:
        raise ValueError(f"{name} must be a non-string iterable") from exc
    result: list[float] = []
    for index, item in enumerate(items):
        result.append(_as_float(item, f"{name}[{index}]"))
    return result


def _as_mapping(value: object, name: str) -> Mapping[str, object]:
    """Require a mapping input."""
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return cast(Mapping[str, object], value)


def _finite_result(value: float, name: str) -> float:
    """Require a finite computed result."""
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return float(value)


def compute_stored_energy(state: object) -> float:
    """Compute stored energy from inductor, capacitor, and mutual terms."""
    data = _as_mapping(state, "state")

    required = ("i_L", "L", "v_C", "C")
    for key in required:
        if key not in data:
            raise ValueError(f"state missing key: {key}")

    currents = _as_float_list(data["i_L"], "state['i_L']")
    inductances = _as_float_list(data["L"], "state['L']")
    voltages = _as_float_list(data["v_C"], "state['v_C']")
    capacitances = _as_float_list(data["C"], "state['C']")

    if len(currents) != len(inductances):
        raise ValueError("state['i_L'] and state['L'] must have same length")
    if len(voltages) != len(capacitances):
        raise ValueError("state['v_C'] and state['C'] must have same length")

    matrix: list[list[float]] | None = None
    if "M" in data:
        raw_matrix = data["M"]
        if isinstance(raw_matrix, (str, bytes)):
            raise ValueError("state['M'] must be a non-string iterable")
        try:
            row_iterable = cast(Iterable[object], raw_matrix)
            rows = iter(row_iterable)
        except TypeError as exc:
            raise ValueError("state['M'] must be a non-string iterable") from exc

        parsed_matrix: list[list[float]] = []
        for row_index, row in enumerate(rows):
            if isinstance(row, (str, bytes)):
                raise ValueError(f"state['M'][{row_index}] must be a non-string iterable")
            try:
                entry_iterable = cast(Iterable[object], row)
                entries = iter(entry_iterable)
            except TypeError as exc:
                raise ValueError(f"state['M'][{row_index}] must be a non-string iterable") from exc
            parsed_row: list[float] = []
            for col_index, entry in enumerate(entries):
                parsed_row.append(_as_float(entry, f"state['M'][{row_index}][{col_index}]"))
            parsed_matrix.append(parsed_row)

        size = len(currents)
        if len(parsed_matrix) != size:
            raise ValueError("state['M'] dimension must equal len(state['i_L'])")
        for row_index, row in enumerate(parsed_matrix):
            if len(row) != size:
                raise ValueError("state['M'] must be square")
            if row[row_index] != 0.0:
                raise ValueError("state['M'] diagonal must be exactly zero")
        for row_index in range(size):
            for col_index in range(size):
                if parsed_matrix[row_index][col_index] != parsed_matrix[col_index][row_index]:
                    raise ValueError("state['M'] must be symmetric")
        matrix = parsed_matrix

    total = 0.0
    for index in range(len(currents)):
        total += 0.5 * inductances[index] * currents[index] * currents[index]
    for index in range(len(voltages)):
        total += 0.5 * capacitances[index] * voltages[index] * voltages[index]
    if matrix is not None:
        coupling = 0.0
        for row_index in range(len(currents)):
            for col_index in range(len(currents)):
                coupling += currents[row_index] * matrix[row_index][col_index] * currents[col_index]
        total += 0.5 * coupling
    return _finite_result(total, "stored energy")


def integrate_power(trace: object) -> float:
    """Integrate sampled power with explicit trapezoidal integration."""
    data = _as_mapping(trace, "trace")
    required = ("v", "i", "t")
    for key in required:
        if key not in data:
            raise ValueError(f"trace missing key: {key}")

    voltages = _as_float_list(data["v"], "trace['v']")
    currents = _as_float_list(data["i"], "trace['i']")
    times = _as_float_list(data["t"], "trace['t']")

    size = len(voltages)
    if size != len(currents) or size != len(times):
        raise ValueError("trace['v'], trace['i'], and trace['t'] must have same length")
    if size < 2:
        raise ValueError("trace samples must have length at least 2")
    for index in range(size - 1):
        if times[index + 1] <= times[index]:
            raise ValueError("trace['t'] must be strictly increasing")

    total = 0.0
    for index in range(size - 1):
        p0 = voltages[index] * currents[index]
        p1 = voltages[index + 1] * currents[index + 1]
        dt = times[index + 1] - times[index]
        total += ((p0 + p1) / 2.0) * dt
    return _finite_result(total, "integrated power")


def compute_residual(ledger: object) -> float:
    """Compute the residual for the locked ledger schema."""
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
        missing = [key for key in required if key not in data]
        extra = [key for key in data.keys() if key not in required]
        if missing:
            raise ValueError(f"ledger missing key: {missing[0]}")
        raise ValueError(f"ledger has unknown key: {extra[0]}")

    values: dict[str, float] = {}
    for key in required:
        values[key] = _as_float(data[key], f"ledger['{key}']")

    delta_stored = values["E_stored_t1"] - values["E_stored_t0"]
    residual = values["E_driver"] - (
        values["E_load"] + values["E_R"] + values["E_rad"] + values["E_parasitic"] + delta_stored
    )
    return _finite_result(residual, "residual")


def classify_run(ledger: object, tau: float) -> str:
    """Classify a run from the residual threshold only."""
    threshold = _as_float(tau, "tau")
    if threshold < 0.0:
        raise ValueError("tau must be >= 0")

    residual = compute_residual(ledger)
    if abs(residual) <= threshold:
        return "CLOSED"
    if residual > threshold:
        return "UNDERACCOUNTED"
    return "APPARENT_EXCESS"
