from __future__ import annotations

import pytest

from experiment.uncertainty_budget import missing_uncertainty_channels, normalize_uncertainty_budget


def test_normalize_uncertainty_budget_returns_all_components() -> None:
    budget = {
        "channels": {
            "driver_trace": {
                "gain": 0.01,
                "offset": 0.001,
                "timing": 1e-9,
                "phase": 0.05,
                "bandwidth": 1000.0,
            }
        }
    }

    normalized = normalize_uncertainty_budget(budget)

    assert normalized == budget


def test_missing_uncertainty_channels_reports_gaps() -> None:
    budget = {
        "channels": {
            "driver_trace": {
                "gain": 0.01,
                "offset": 0.001,
                "timing": 1e-9,
                "phase": 0.05,
                "bandwidth": 1000.0,
            }
        }
    }

    assert missing_uncertainty_channels(budget, ["driver_trace", "load_trace"]) == ["load_trace"]


def test_normalize_uncertainty_budget_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        normalize_uncertainty_budget(
            {
                "channels": {
                    "driver_trace": {
                        "gain": -0.01,
                        "offset": 0.0,
                        "timing": 0.0,
                        "phase": 0.0,
                        "bandwidth": 1.0,
                    }
                }
            }
        )
