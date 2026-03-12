from __future__ import annotations

from experiment.hidden_source_checks import normalize_hidden_source_observations, run_hidden_source_checks


def _boundary_map() -> dict[str, object]:
    return {
        "setup_id": "bench_v1",
        "ingress": [
            {
                "name": "driver_supply",
                "kind": "electrical",
                "metered": True,
                "channels": ["driver_trace"],
            }
        ],
        "egress": [
            {
                "name": "load",
                "kind": "electrical",
                "metered": True,
                "channels": ["load_trace"],
            }
        ],
    }


def test_normalize_hidden_source_observations_accepts_known_flags() -> None:
    observations = normalize_hidden_source_observations(
        {
            "artifact_flags": ["aliasing", "dc_offset"],
            "suspected_sources": ["precharged capacitor"],
            "boundary_violations": ["ground bypass"],
            "notes": "bench capture",
        }
    )

    assert observations["artifact_flags"] == ["aliasing", "dc_offset"]
    assert observations["suspected_sources"] == ["precharged capacitor"]


def test_run_hidden_source_checks_collects_findings() -> None:
    result = run_hidden_source_checks(
        _boundary_map(),
        observations={
            "artifact_flags": ["phase_misalignment"],
            "suspected_sources": ["aux battery"],
            "boundary_violations": ["fixture bypass"],
        },
        observed_channels=["driver_trace"],
    )

    assert result["passed"] is False
    assert result["reasons"] == [
        "egress point 'load' missing observed channel: load_trace",
        "suspected hidden source: aux battery",
        "boundary violation: fixture bypass",
        "artifact challenge failed: phase_misalignment",
    ]
