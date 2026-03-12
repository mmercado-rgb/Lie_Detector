from __future__ import annotations

import math

import pytest

from experiment.energy_ledger import classify_run, compute_residual, compute_stored_energy, integrate_power


def test_compute_stored_energy_without_mutual_inductance() -> None:
    state = {
        "i_L": [2.0, -1.0],
        "L": [3.0, 5.0],
        "v_C": [4.0],
        "C": [2.0],
    }

    result = compute_stored_energy(state)

    expected = 0.5 * 3.0 * 2.0**2 + 0.5 * 5.0 * (-1.0) ** 2 + 0.5 * 2.0 * 4.0**2
    assert result == pytest.approx(expected)


def test_compute_stored_energy_with_mutual_inductance() -> None:
    state = {
        "i_L": [1.0, -2.0],
        "L": [2.0, 4.0],
        "v_C": [3.0],
        "C": [5.0],
        "M": [
            [0.0, 0.5],
            [0.5, 0.0],
        ],
    }

    result = compute_stored_energy(state)

    self_terms = 0.5 * 2.0 * 1.0**2 + 0.5 * 4.0 * (-2.0) ** 2 + 0.5 * 5.0 * 3.0**2
    mutual_term = 0.5 * ((1.0 * 0.0 * 1.0) + (1.0 * 0.5 * -2.0) + (-2.0 * 0.5 * 1.0) + (-2.0 * 0.0 * -2.0))
    assert result == pytest.approx(self_terms + mutual_term)


def test_compute_stored_energy_rejects_mismatched_inductor_lengths() -> None:
    state = {
        "i_L": [1.0, 2.0],
        "L": [3.0],
        "v_C": [4.0],
        "C": [5.0],
    }

    with pytest.raises(ValueError):
        compute_stored_energy(state)


def test_compute_stored_energy_rejects_mismatched_capacitor_lengths() -> None:
    state = {
        "i_L": [1.0],
        "L": [3.0],
        "v_C": [4.0, 5.0],
        "C": [6.0],
    }

    with pytest.raises(ValueError):
        compute_stored_energy(state)


def test_compute_stored_energy_rejects_missing_required_key() -> None:
    state = {
        "i_L": [1.0],
        "L": [2.0],
        "v_C": [3.0],
    }

    with pytest.raises(ValueError):
        compute_stored_energy(state)


def test_compute_stored_energy_rejects_nonfinite_value() -> None:
    state = {
        "i_L": [1.0],
        "L": [math.inf],
        "v_C": [3.0],
        "C": [4.0],
    }

    with pytest.raises(ValueError):
        compute_stored_energy(state)


def test_compute_stored_energy_rejects_invalid_mutual_matrix_shape() -> None:
    state = {
        "i_L": [1.0, 2.0],
        "L": [3.0, 4.0],
        "v_C": [5.0],
        "C": [6.0],
        "M": [[0.0, 1.0]],
    }

    with pytest.raises(ValueError):
        compute_stored_energy(state)


def test_compute_stored_energy_rejects_nonsymmetric_mutual_matrix() -> None:
    state = {
        "i_L": [1.0, 2.0],
        "L": [3.0, 4.0],
        "v_C": [5.0],
        "C": [6.0],
        "M": [
            [0.0, 1.0],
            [2.0, 0.0],
        ],
    }

    with pytest.raises(ValueError):
        compute_stored_energy(state)


def test_compute_stored_energy_rejects_nonzero_mutual_matrix_diagonal() -> None:
    state = {
        "i_L": [1.0, 2.0],
        "L": [3.0, 4.0],
        "v_C": [5.0],
        "C": [6.0],
        "M": [
            [1.0, 0.5],
            [0.5, 0.0],
        ],
    }

    with pytest.raises(ValueError):
        compute_stored_energy(state)


def test_integrate_power_valid_trace() -> None:
    trace = {
        "v": [1.0, 3.0, 5.0],
        "i": [2.0, 2.0, 4.0],
        "t": [0.0, 1.0, 3.0],
    }

    result = integrate_power(trace)

    expected = ((2.0 + 6.0) / 2.0) * 1.0 + ((6.0 + 20.0) / 2.0) * 2.0
    assert result == pytest.approx(expected)


def test_integrate_power_rejects_mismatched_lengths() -> None:
    trace = {
        "v": [1.0, 2.0],
        "i": [3.0],
        "t": [0.0, 1.0],
    }

    with pytest.raises(ValueError):
        integrate_power(trace)


def test_integrate_power_rejects_short_trace() -> None:
    trace = {
        "v": [1.0],
        "i": [2.0],
        "t": [0.0],
    }

    with pytest.raises(ValueError):
        integrate_power(trace)


def test_integrate_power_rejects_non_monotonic_time() -> None:
    trace = {
        "v": [1.0, 2.0],
        "i": [3.0, 4.0],
        "t": [0.0, 0.0],
    }

    with pytest.raises(ValueError):
        integrate_power(trace)


def test_integrate_power_rejects_nonfinite_value() -> None:
    trace = {
        "v": [1.0, math.nan],
        "i": [3.0, 4.0],
        "t": [0.0, 1.0],
    }

    with pytest.raises(ValueError):
        integrate_power(trace)


def test_integrate_power_rejects_missing_key() -> None:
    trace = {
        "v": [1.0, 2.0],
        "i": [3.0, 4.0],
    }

    with pytest.raises(ValueError):
        integrate_power(trace)


def test_compute_residual_valid_ledger() -> None:
    ledger = {
        "E_driver": 12.0,
        "E_load": 5.0,
        "E_R": 2.0,
        "E_rad": 1.0,
        "E_parasitic": 0.5,
        "E_stored_t0": 1.0,
        "E_stored_t1": 3.0,
    }

    result = compute_residual(ledger)

    expected = 12.0 - (5.0 + 2.0 + 1.0 + 0.5 + (3.0 - 1.0))
    assert result == pytest.approx(expected)


def test_compute_residual_rejects_missing_key() -> None:
    ledger = {
        "E_driver": 1.0,
        "E_load": 2.0,
        "E_R": 3.0,
        "E_rad": 4.0,
        "E_parasitic": 5.0,
        "E_stored_t0": 6.0,
    }

    with pytest.raises(ValueError):
        compute_residual(ledger)


def test_compute_residual_rejects_nonfinite_value() -> None:
    ledger = {
        "E_driver": 1.0,
        "E_load": 2.0,
        "E_R": 3.0,
        "E_rad": math.inf,
        "E_parasitic": 5.0,
        "E_stored_t0": 6.0,
        "E_stored_t1": 7.0,
    }

    with pytest.raises(ValueError):
        compute_residual(ledger)


def test_classify_run_returns_closed() -> None:
    ledger = {
        "E_driver": 10.0,
        "E_load": 4.0,
        "E_R": 2.0,
        "E_rad": 1.0,
        "E_parasitic": 1.0,
        "E_stored_t0": 1.0,
        "E_stored_t1": 3.0,
    }

    assert classify_run(ledger, 0.0) == "CLOSED"


def test_classify_run_returns_underaccounted() -> None:
    ledger = {
        "E_driver": 10.0,
        "E_load": 3.0,
        "E_R": 2.0,
        "E_rad": 1.0,
        "E_parasitic": 1.0,
        "E_stored_t0": 1.0,
        "E_stored_t1": 3.0,
    }

    assert classify_run(ledger, 0.5) == "UNDERACCOUNTED"


def test_classify_run_returns_apparent_excess() -> None:
    ledger = {
        "E_driver": 6.0,
        "E_load": 4.0,
        "E_R": 2.0,
        "E_rad": 1.0,
        "E_parasitic": 1.0,
        "E_stored_t0": 1.0,
        "E_stored_t1": 3.0,
    }

    assert classify_run(ledger, 0.5) == "APPARENT_EXCESS"


def test_classify_run_rejects_negative_tau() -> None:
    ledger = {
        "E_driver": 10.0,
        "E_load": 4.0,
        "E_R": 2.0,
        "E_rad": 1.0,
        "E_parasitic": 1.0,
        "E_stored_t0": 1.0,
        "E_stored_t1": 3.0,
    }

    with pytest.raises(ValueError):
        classify_run(ledger, -0.1)


def test_classify_run_rejects_nonfinite_tau() -> None:
    ledger = {
        "E_driver": 10.0,
        "E_load": 4.0,
        "E_R": 2.0,
        "E_rad": 1.0,
        "E_parasitic": 1.0,
        "E_stored_t0": 1.0,
        "E_stored_t1": 3.0,
    }

    with pytest.raises(ValueError):
        classify_run(ledger, math.inf)
