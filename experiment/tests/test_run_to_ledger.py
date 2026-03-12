from __future__ import annotations

import pytest

from experiment.energy_ledger import classify_run, compute_residual
from experiment.run_to_ledger import build_ledger


def test_build_ledger_end_to_end_closed_run() -> None:
    run_data = {
        "driver_trace": {"v": [5.0, 5.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
        "load_trace": {"v": [3.0, 3.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
        "resistor_traces": [{"v": [1.0, 1.0], "i": [1.0, 1.0], "t": [0.0, 1.0]}],
        "E_rad": 0.5,
        "E_parasitic": 0.5,
        "state_t0": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
        "state_t1": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
    }

    ledger = build_ledger(run_data)

    assert list(ledger.keys()) == [
        "E_driver",
        "E_load",
        "E_R",
        "E_rad",
        "E_parasitic",
        "E_stored_t0",
        "E_stored_t1",
    ]
    assert ledger == pytest.approx(
        {
            "E_driver": 5.0,
            "E_load": 3.0,
            "E_R": 1.0,
            "E_rad": 0.5,
            "E_parasitic": 0.5,
            "E_stored_t0": 0.0,
            "E_stored_t1": 0.0,
        }
    )

    residual = compute_residual(ledger)
    label = classify_run(ledger, 1e-9)

    assert residual == pytest.approx(0.0)
    assert label == "CLOSED"


def test_build_ledger_rejects_missing_required_key() -> None:
    run_data = {
        "driver_trace": {"v": [5.0, 5.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
        "load_trace": {"v": [3.0, 3.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
        "resistor_traces": [{"v": [1.0, 1.0], "i": [1.0, 1.0], "t": [0.0, 1.0]}],
        "E_rad": 0.5,
        "state_t0": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
        "state_t1": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
    }

    with pytest.raises(ValueError):
        build_ledger(run_data)
