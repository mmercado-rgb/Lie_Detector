from __future__ import annotations

from experiment.artifact_library import get_artifact_scenario, list_artifact_scenarios
from experiment.batch_runner import run_batch


def test_artifact_library_lists_expected_false_positive_scenarios() -> None:
    scenario_names = [scenario["name"] for scenario in list_artifact_scenarios()]

    assert scenario_names == [
        "aliasing",
        "capacitor_precharge",
        "dc_offset",
        "hidden_ground_return",
        "missed_recharge_window",
        "phase_misalignment",
        "thermal_lag",
    ]


def test_artifact_library_reproduces_known_false_positives() -> None:
    for scenario in list_artifact_scenarios():
        result = run_batch([scenario["run_data"]], tau=1e-9)[0]
        assert result["label"] == "APPARENT_EXCESS"
        assert result["residual"] < 0


def test_get_artifact_scenario_returns_copy() -> None:
    first = get_artifact_scenario("aliasing")
    second = get_artifact_scenario("aliasing")

    first["name"] = "changed"

    assert second["name"] == "aliasing"
