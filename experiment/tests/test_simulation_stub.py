from __future__ import annotations

import pytest

from experiment.energy_ledger import classify_run, compute_residual
from experiment.run_to_ledger import build_ledger
from experiment.simulation_stub import make_closed_run_data


def test_closed_stub_pipeline() -> None:
    run_data = make_closed_run_data()
    ledger = build_ledger(run_data)
    rho = compute_residual(ledger)
    label = classify_run(ledger, 1e-9)

    assert list(ledger.keys()) == [
        "E_driver",
        "E_load",
        "E_R",
        "E_rad",
        "E_parasitic",
        "E_stored_t0",
        "E_stored_t1",
    ]
    assert rho == pytest.approx(0.0)
    assert label == "CLOSED"
