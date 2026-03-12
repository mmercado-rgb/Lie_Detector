"""Normalize raw instrument exports into canonical trace records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast


_TIME_ALIASES = ("t", "time", "time_s", "seconds", "timestamp_s")
_VOLTAGE_ALIASES = ("v", "voltage", "voltage_v", "volts")
_CURRENT_ALIASES = ("i", "current", "current_a", "amps")


def _as_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return cast(Mapping[str, object], value)


def _as_iterable(value: object, name: str) -> list[object]:
    if isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{name} must be a non-string iterable")
    try:
        return list(cast(Iterable[object], value))
    except TypeError as exc:
        raise ValueError(f"{name} must be a non-string iterable") from exc


def _as_text(value: object, name: str, default: str) -> str:
    if value is None:
        return default
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


def _find_alias(data: Mapping[str, object], aliases: tuple[str, ...], name: str) -> object:
    for alias in aliases:
        if alias in data:
            return data[alias]
    raise ValueError(f"{name} missing required channel")


def _normalize_columnar_export(data: Mapping[str, object], name: str) -> tuple[list[float], list[float], list[float]]:
    times = [_as_float(item, f"{name}['time']") for item in _as_iterable(_find_alias(data, _TIME_ALIASES, name), f"{name}['time']")]
    voltages = [_as_float(item, f"{name}['voltage']") for item in _as_iterable(_find_alias(data, _VOLTAGE_ALIASES, name), f"{name}['voltage']")]
    currents = [_as_float(item, f"{name}['current']") for item in _as_iterable(_find_alias(data, _CURRENT_ALIASES, name), f"{name}['current']")]
    return times, voltages, currents


def _read_row_value(row: Mapping[str, object], aliases: tuple[str, ...], name: str) -> float:
    for alias in aliases:
        if alias in row:
            return _as_float(row[alias], f"{name}['{alias}']")
    raise ValueError(f"{name} missing required field")


def _normalize_row_export(data: Mapping[str, object], name: str) -> tuple[list[float], list[float], list[float]]:
    samples = _as_iterable(data["samples"], f"{name}['samples']")
    if len(samples) < 2:
        raise ValueError(f"{name}['samples'] must contain at least 2 rows")

    times: list[float] = []
    voltages: list[float] = []
    currents: list[float] = []
    for index, sample in enumerate(samples):
        row = _as_mapping(sample, f"{name}['samples'][{index}]")
        times.append(_read_row_value(row, _TIME_ALIASES, f"{name}['samples'][{index}]"))
        voltages.append(_read_row_value(row, _VOLTAGE_ALIASES, f"{name}['samples'][{index}]"))
        currents.append(_read_row_value(row, _CURRENT_ALIASES, f"{name}['samples'][{index}]"))
    return times, voltages, currents


def _validate_trace_lengths(times: list[float], voltages: list[float], currents: list[float], name: str) -> None:
    if len(times) != len(voltages) or len(times) != len(currents):
        raise ValueError(f"{name} channels must have the same length")
    if len(times) < 2:
        raise ValueError(f"{name} must contain at least 2 samples")
    for index in range(len(times) - 1):
        if times[index + 1] <= times[index]:
            raise ValueError(f"{name} timebase must be strictly increasing")


def normalize_measurement_export(raw_export: object) -> dict[str, object]:
    """Normalize one raw export into the canonical t/v/i trace schema."""
    data = _as_mapping(raw_export, "raw_export")

    if "samples" in data:
        times, voltages, currents = _normalize_row_export(data, "raw_export")
        source_format = _as_text(data.get("source_format"), "raw_export['source_format']", "row_samples")
    else:
        times, voltages, currents = _normalize_columnar_export(data, "raw_export")
        source_format = _as_text(data.get("source_format"), "raw_export['source_format']", "columnar")

    _validate_trace_lengths(times, voltages, currents, "raw_export")

    channel_id = _as_text(data.get("channel_id"), "raw_export['channel_id']", "trace")
    trace_id = _as_text(data.get("trace_id"), "raw_export['trace_id']", channel_id)

    sample_rate_hz: float | None = None
    if "sample_rate_hz" in data:
        sample_rate_hz = _as_float(data["sample_rate_hz"], "raw_export['sample_rate_hz']")
        if sample_rate_hz <= 0.0:
            raise ValueError("raw_export['sample_rate_hz'] must be > 0")

    return {
        "trace_id": trace_id,
        "channel_id": channel_id,
        "source_format": source_format,
        "t": times,
        "v": voltages,
        "i": currents,
        "sample_rate_hz": sample_rate_hz,
    }


def normalize_measurement_bundle(raw_measurements: object) -> dict[str, object]:
    """Normalize a run's measurement bundle into phase-1 compatible traces."""
    data = _as_mapping(raw_measurements, "raw_measurements")
    required = ("driver_trace", "load_trace", "resistor_traces")
    for key in required:
        if key not in data:
            raise ValueError(f"raw_measurements missing key: {key}")

    resistor_traces = _as_iterable(data["resistor_traces"], "raw_measurements['resistor_traces']")
    return {
        "driver_trace": normalize_measurement_export(data["driver_trace"]),
        "load_trace": normalize_measurement_export(data["load_trace"]),
        "resistor_traces": [
            normalize_measurement_export(trace) for trace in resistor_traces
        ],
    }
