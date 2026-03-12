from __future__ import annotations

import pytest

from experiment.batch_runner import run_batch
from experiment.simulation_variants import (
    make_apparent_excess_run_data,
    make_closed_run_data,
    make_underaccounted_run_data,
)


def test_run_batch_three_scenarios_in_order() -> None:
    results = run_batch(
        [
            make_closed_run_data(),
            make_underaccounted_run_data(),
            make_apparent_excess_run_data(),
        ],
        tau=1e-9,
    )

    assert len(results) == 3
    assert [set(result.keys()) == {"ledger", "residual", "label"} for result in results] == [True, True, True]
    assert [result["label"] for result in results] == ["CLOSED", "UNDERACCOUNTED", "APPARENT_EXCESS"]
    assert results[0]["residual"] == pytest.approx(0.0)
    assert results[1]["residual"] > 0
    assert results[2]["residual"] < 0


def test_run_batch_returns_expected_result_shape() -> None:
    results = run_batch(
        [
            make_closed_run_data(),
        ],
        tau=1e-9,
    )

    assert len(results) == 1
    assert set(results[0].keys()) == {"ledger", "residual", "label"}
    assert results[0]["residual"] == pytest.approx(0.0)
    assert results[0]["label"] == "CLOSED"


def test_run_batch_invalid_tau_raises() -> None:
    with pytest.raises(ValueError):
        run_batch([make_closed_run_data()], tau=-1.0)

    with pytest.raises(ValueError):
        run_batch([make_closed_run_data()], tau=float("inf"))
