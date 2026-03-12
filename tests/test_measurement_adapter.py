from __future__ import annotations

from collections.abc import Mapping, Sequence

import pytest

from experiment.measurement_adapter import normalize_measurement_bundle, normalize_measurement_export


def test_normalize_measurement_export_handles_columnar_aliases() -> None:
    raw_export = {
        "trace_id": "driver-v-i",
        "channel_id": "driver_trace",
        "source_format": "scope_csv",
        "time_s": [0.0, 1.0],
        "voltage_v": [5.0, 5.0],
        "current_a": [1.0, 1.0],
        "sample_rate_hz": "1000000",
    }

    normalized = normalize_measurement_export(raw_export)

    assert normalized == {
        "trace_id": "driver-v-i",
        "channel_id": "driver_trace",
        "source_format": "scope_csv",
        "t": [0.0, 1.0],
        "v": [5.0, 5.0],
        "i": [1.0, 1.0],
        "sample_rate_hz": 1000000.0,
    }


def test_normalize_measurement_bundle_handles_row_samples() -> None:
    raw_measurements = {
        "driver_trace": {
            "channel_id": "driver_trace",
            "samples": [
                {"time_s": 0.0, "voltage_v": 5.0, "current_a": 1.0},
                {"time_s": 1.0, "voltage_v": 5.0, "current_a": 1.0},
            ],
        },
        "load_trace": {
            "channel_id": "load_trace",
            "t": [0.0, 1.0],
            "v": [3.0, 3.0],
            "i": [1.0, 1.0],
        },
        "resistor_traces": [
            {
                "channel_id": "resistor_trace_0",
                "samples": [
                    {"t": 0.0, "v": 1.0, "i": 1.0},
                    {"t": 1.0, "v": 1.0, "i": 1.0},
                ],
            }
        ],
    }

    normalized = normalize_measurement_bundle(raw_measurements)
    driver_trace = normalized["driver_trace"]
    load_trace = normalized["load_trace"]
    resistor_traces = normalized["resistor_traces"]

    assert isinstance(driver_trace, Mapping)
    assert isinstance(load_trace, Mapping)
    assert isinstance(resistor_traces, Sequence)
    assert resistor_traces

    resistor_trace = resistor_traces[0]
    assert isinstance(resistor_trace, Mapping)

    assert driver_trace["t"] == [0.0, 1.0]
    assert load_trace["v"] == [3.0, 3.0]
    assert resistor_trace["i"] == [1.0, 1.0]


def test_normalize_measurement_export_rejects_non_monotonic_timebase() -> None:
    with pytest.raises(ValueError):
        normalize_measurement_export(
            {
                "t": [0.0, 0.0],
                "v": [1.0, 1.0],
                "i": [1.0, 1.0],
            }
        )
