"""Deterministic run-data stub for a closed ledger example."""

from __future__ import annotations


def make_closed_run_data() -> dict[str, object]:
    return {
        "driver_trace": {"v": [5.0, 5.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
        "load_trace": {"v": [3.0, 3.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
        "resistor_traces": [{"v": [1.0, 1.0], "i": [1.0, 1.0], "t": [0.0, 1.0]}],
        "E_rad": 0.5,
        "E_parasitic": 0.5,
        "state_t0": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
        "state_t1": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
    }
