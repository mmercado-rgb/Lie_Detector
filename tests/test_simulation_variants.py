from __future__ import annotations

import pytest

from experiment.energy_ledger import classify_run, compute_residual
from experiment.run_to_ledger import build_ledger
from experiment.simulation_variants import (
    make_apparent_excess_run_data,
    make_closed_run_data,
    make_underaccounted_run_data,
)


def test_closed_scenario_classifies_closed() -> None:
    run_data = make_closed_run_data()
    ledger = build_ledger(run_data)
    residual = compute_residual(ledger)
    label = classify_run(ledger, tau=1e-9)

    assert label == "CLOSED"
    assert residual == pytest.approx(0.0)


def test_underaccounted_scenario_classifies_underaccounted() -> None:
    run_data = make_underaccounted_run_data()
    ledger = build_ledger(run_data)
    residual = compute_residual(ledger)
    label = classify_run(ledger, tau=1e-9)

    assert label == "UNDERACCOUNTED"
    assert residual > 0


def test_apparent_excess_scenario_classifies_apparent_excess() -> None:
    run_data = make_apparent_excess_run_data()
    ledger = build_ledger(run_data)
    residual = compute_residual(ledger)
    label = classify_run(ledger, tau=1e-9)

    assert label == "APPARENT_EXCESS"
    assert residual < 0
