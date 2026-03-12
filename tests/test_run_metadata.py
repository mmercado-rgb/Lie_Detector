from __future__ import annotations

import pytest

from experiment.run_metadata import normalize_run_metadata


def test_normalize_run_metadata_returns_locked_schema() -> None:
    metadata = {
        "device_ids": {"scope": "SCOPE-01", "probe": "HV-07"},
        "operator": "Ada Lovelace",
        "timestamp": "2026-03-11T16:45:00Z",
        "calibration_ids": {"scope": "CAL-2026-001", "probe": "CAL-2026-002"},
        "ambient_conditions": {"temperature_c": 22.5, "humidity_pct": "41.0"},
        "sample_rates": {"driver_trace": 1000000, "load_trace": "500000"},
        "comments": " bench run ",
    }

    normalized = normalize_run_metadata(metadata)

    assert normalized == {
        "device_ids": {"scope": "SCOPE-01", "probe": "HV-07"},
        "operator": "Ada Lovelace",
        "timestamp": "2026-03-11T16:45:00+00:00",
        "calibration_ids": {"scope": "CAL-2026-001", "probe": "CAL-2026-002"},
        "ambient_conditions": {"temperature_c": 22.5, "humidity_pct": 41.0},
        "sample_rates": {"driver_trace": 1000000.0, "load_trace": 500000.0},
        "comments": "bench run",
    }


def test_normalize_run_metadata_rejects_missing_or_invalid_fields() -> None:
    with pytest.raises(ValueError):
        normalize_run_metadata(
            {
                "device_ids": {"scope": "SCOPE-01"},
                "operator": "Ada Lovelace",
                "timestamp": "2026-03-11T16:45:00",
                "calibration_ids": {"scope": "CAL-2026-001"},
                "ambient_conditions": {"temperature_c": 22.5},
                "sample_rates": {"driver_trace": 0},
                "comments": "",
            }
        )
