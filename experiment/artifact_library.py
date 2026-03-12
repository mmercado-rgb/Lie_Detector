"""Deterministic false-positive scenarios used for adversarial checks."""

from __future__ import annotations

from copy import deepcopy


_SCENARIOS: dict[str, dict[str, object]] = {
    "aliasing": {
        "name": "aliasing",
        "description": "Sample aliasing inflates apparent delivered output despite fixed driver input.",
        "run_data": {
            "driver_trace": {"v": [5.0, 5.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "load_trace": {"v": [4.6, 4.6], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "resistor_traces": [{"v": [0.7, 0.7], "i": [1.0, 1.0], "t": [0.0, 1.0]}],
            "E_rad": 0.15,
            "E_parasitic": 0.05,
            "state_t0": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
            "state_t1": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
        },
        "boundary_map": {
            "setup_id": "artifact_aliasing_bench",
            "ingress": [
                {
                    "name": "driver_supply",
                    "kind": "electrical",
                    "metered": True,
                    "channels": ["driver_trace"],
                }
            ],
            "egress": [
                {"name": "load", "kind": "electrical", "metered": True, "channels": ["load_trace"]},
                {
                    "name": "resistor_bank",
                    "kind": "thermal",
                    "metered": True,
                    "channels": ["resistor_trace_0"],
                },
            ],
        },
        "hidden_source_observations": {
            "artifact_flags": ["aliasing"],
            "suspected_sources": [],
            "boundary_violations": [],
            "notes": "Known undersampled switching waveform.",
        },
    },
    "phase_misalignment": {
        "name": "phase_misalignment",
        "description": "Probe skew creates a phase error that makes power appear negative at the source.",
        "run_data": {
            "driver_trace": {"v": [5.0, 5.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "load_trace": {"v": [4.4, 4.4], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "resistor_traces": [{"v": [0.8, 0.8], "i": [1.0, 1.0], "t": [0.0, 1.0]}],
            "E_rad": 0.2,
            "E_parasitic": 0.1,
            "state_t0": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
            "state_t1": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
        },
        "boundary_map": {
            "setup_id": "artifact_phase_bench",
            "ingress": [
                {
                    "name": "driver_supply",
                    "kind": "electrical",
                    "metered": True,
                    "channels": ["driver_trace"],
                }
            ],
            "egress": [
                {"name": "load", "kind": "electrical", "metered": True, "channels": ["load_trace"]},
                {
                    "name": "resistor_bank",
                    "kind": "thermal",
                    "metered": True,
                    "channels": ["resistor_trace_0"],
                },
            ],
        },
        "hidden_source_observations": {
            "artifact_flags": ["phase_misalignment"],
            "suspected_sources": [],
            "boundary_violations": [],
            "notes": "",
        },
    },
    "dc_offset": {
        "name": "dc_offset",
        "description": "Offset bias in one probe inflates integrated energy.",
        "run_data": {
            "driver_trace": {"v": [5.0, 5.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "load_trace": {"v": [3.8, 3.8], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "resistor_traces": [{"v": [1.4, 1.4], "i": [1.0, 1.0], "t": [0.0, 1.0]}],
            "E_rad": 0.2,
            "E_parasitic": 0.1,
            "state_t0": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
            "state_t1": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
        },
        "boundary_map": {
            "setup_id": "artifact_dc_offset_bench",
            "ingress": [
                {
                    "name": "driver_supply",
                    "kind": "electrical",
                    "metered": True,
                    "channels": ["driver_trace"],
                }
            ],
            "egress": [
                {"name": "load", "kind": "electrical", "metered": True, "channels": ["load_trace"]},
                {
                    "name": "resistor_bank",
                    "kind": "thermal",
                    "metered": True,
                    "channels": ["resistor_trace_0"],
                },
            ],
        },
        "hidden_source_observations": {
            "artifact_flags": ["dc_offset"],
            "suspected_sources": [],
            "boundary_violations": [],
            "notes": "",
        },
    },
    "missed_recharge_window": {
        "name": "missed_recharge_window",
        "description": "Driver recharge energy is omitted from the accounting window.",
        "run_data": {
            "driver_trace": {"v": [5.0, 5.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "load_trace": {"v": [4.0, 4.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "resistor_traces": [{"v": [1.0, 1.0], "i": [1.0, 1.0], "t": [0.0, 1.0]}],
            "E_rad": 0.2,
            "E_parasitic": 0.1,
            "state_t0": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
            "state_t1": {"i_L": [0.0], "L": [1.0], "v_C": [1.0], "C": [1.0]},
        },
        "boundary_map": {
            "setup_id": "artifact_recharge_bench",
            "ingress": [
                {
                    "name": "driver_supply",
                    "kind": "electrical",
                    "metered": True,
                    "channels": ["driver_trace"],
                }
            ],
            "egress": [
                {"name": "load", "kind": "electrical", "metered": True, "channels": ["load_trace"]},
                {
                    "name": "resistor_bank",
                    "kind": "thermal",
                    "metered": True,
                    "channels": ["resistor_trace_0"],
                },
            ],
        },
        "hidden_source_observations": {
            "artifact_flags": ["missed_recharge_window"],
            "suspected_sources": ["unmetered recharge cycle"],
            "boundary_violations": [],
            "notes": "",
        },
    },
    "hidden_ground_return": {
        "name": "hidden_ground_return",
        "description": "Bench ground return bypasses the declared metered input path.",
        "run_data": {
            "driver_trace": {"v": [5.0, 5.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "load_trace": {"v": [4.3, 4.3], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "resistor_traces": [{"v": [1.0, 1.0], "i": [1.0, 1.0], "t": [0.0, 1.0]}],
            "E_rad": 0.15,
            "E_parasitic": 0.1,
            "state_t0": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
            "state_t1": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
        },
        "boundary_map": {
            "setup_id": "artifact_ground_return_bench",
            "ingress": [
                {
                    "name": "driver_supply",
                    "kind": "electrical",
                    "metered": True,
                    "channels": ["driver_trace"],
                },
                {
                    "name": "bench_ground",
                    "kind": "return_path",
                    "metered": False,
                    "channels": [],
                },
            ],
            "egress": [
                {"name": "load", "kind": "electrical", "metered": True, "channels": ["load_trace"]},
                {
                    "name": "resistor_bank",
                    "kind": "thermal",
                    "metered": True,
                    "channels": ["resistor_trace_0"],
                },
            ],
        },
        "hidden_source_observations": {
            "artifact_flags": ["hidden_ground_return"],
            "suspected_sources": [],
            "boundary_violations": ["bench ground bypass"],
            "notes": "",
        },
    },
    "capacitor_precharge": {
        "name": "capacitor_precharge",
        "description": "A precharged capacitor injects energy that the initial state declaration missed.",
        "run_data": {
            "driver_trace": {"v": [5.0, 5.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "load_trace": {"v": [4.35, 4.35], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "resistor_traces": [{"v": [0.85, 0.85], "i": [1.0, 1.0], "t": [0.0, 1.0]}],
            "E_rad": 0.2,
            "E_parasitic": 0.1,
            "state_t0": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
            "state_t1": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
        },
        "boundary_map": {
            "setup_id": "artifact_precharge_bench",
            "ingress": [
                {
                    "name": "driver_supply",
                    "kind": "electrical",
                    "metered": True,
                    "channels": ["driver_trace"],
                }
            ],
            "egress": [
                {"name": "load", "kind": "electrical", "metered": True, "channels": ["load_trace"]},
                {
                    "name": "resistor_bank",
                    "kind": "thermal",
                    "metered": True,
                    "channels": ["resistor_trace_0"],
                },
            ],
        },
        "hidden_source_observations": {
            "artifact_flags": ["capacitor_precharge"],
            "suspected_sources": ["precharged storage element"],
            "boundary_violations": [],
            "notes": "",
        },
    },
    "thermal_lag": {
        "name": "thermal_lag",
        "description": "Slow calorimeter response creates a transient apparent excess that disappears on cross-check.",
        "run_data": {
            "driver_trace": {"v": [5.0, 5.0], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "load_trace": {"v": [4.5, 4.5], "i": [1.0, 1.0], "t": [0.0, 1.0]},
            "resistor_traces": [{"v": [0.7, 0.7], "i": [1.0, 1.0], "t": [0.0, 1.0]}],
            "E_rad": 0.2,
            "E_parasitic": 0.15,
            "state_t0": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
            "state_t1": {"i_L": [0.0], "L": [1.0], "v_C": [0.0], "C": [1.0]},
        },
        "boundary_map": {
            "setup_id": "artifact_thermal_lag_bench",
            "ingress": [
                {
                    "name": "driver_supply",
                    "kind": "electrical",
                    "metered": True,
                    "channels": ["driver_trace"],
                }
            ],
            "egress": [
                {"name": "load", "kind": "electrical", "metered": True, "channels": ["load_trace"]},
                {
                    "name": "resistor_bank",
                    "kind": "thermal",
                    "metered": True,
                    "channels": ["resistor_trace_0"],
                },
            ],
        },
        "hidden_source_observations": {
            "artifact_flags": ["thermal_lag"],
            "suspected_sources": [],
            "boundary_violations": [],
            "notes": "",
        },
        "cross_check_data": {
            "calorimetry": {"observed_output_energy": 4.85, "tolerance": 0.05},
        },
    },
}


def list_artifact_scenarios() -> list[dict[str, object]]:
    """Return deterministic false-positive scenarios used for challenge tests."""
    return [deepcopy(_SCENARIOS[name]) for name in sorted(_SCENARIOS)]


def get_artifact_scenario(name: str) -> dict[str, object]:
    """Return one named deterministic false-positive scenario."""
    scenario_name = name.strip()
    if scenario_name not in _SCENARIOS:
        raise ValueError(f"unknown artifact scenario: {name}")
    return deepcopy(_SCENARIOS[scenario_name])
