from __future__ import annotations

from experiment.cross_checks import evaluate_cross_checks
from experiment.run_to_ledger import build_ledger
from experiment.simulation_variants import make_closed_run_data


def test_evaluate_cross_checks_passes_when_estimates_match() -> None:
    ledger = build_ledger(make_closed_run_data())

    result = evaluate_cross_checks(
        ledger,
        {
            "battery_depletion": {"observed_input_energy": 5.0, "tolerance": 0.05},
            "calorimetry": {"observed_output_energy": 5.0, "tolerance": 0.05},
        },
    )

    assert result["status"] == "PASS"
    assert result["passed"] is True
    assert result["reasons"] == []


def test_evaluate_cross_checks_fails_when_estimates_disagree() -> None:
    ledger = build_ledger(make_closed_run_data())

    result = evaluate_cross_checks(
        ledger,
        {
            "battery_depletion": {"observed_input_energy": 4.7, "tolerance": 0.05},
            "calorimetry": {"observed_output_energy": 5.3, "tolerance": 0.05},
        },
    )

    assert result["status"] == "FAIL"
    assert result["passed"] is False
    assert result["reasons"] == [
        "battery depletion disagrees with electrical driver energy",
        "calorimetry disagrees with electrical ledger output",
    ]
