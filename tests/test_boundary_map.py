from __future__ import annotations

from typing import cast

from experiment.boundary_map import build_boundary_registry, normalize_boundary_map, validate_energy_paths


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
            },
            {
                "name": "resistor_bank",
                "kind": "thermal",
                "metered": True,
                "channels": ["resistor_trace_0"],
            },
        ],
    }


def test_normalize_boundary_map_builds_registry() -> None:
    normalized = normalize_boundary_map(_boundary_map())
    registry = build_boundary_registry(normalized)

    assert normalized["setup_id"] == "bench_v1"
    assert registry["driver_supply"]["direction"] == "ingress"
    assert registry["load"]["channels"] == ["load_trace"]


def test_validate_energy_paths_flags_unmetered_and_missing_channels() -> None:
    boundary_map = _boundary_map()
    ingress = cast(list[object], boundary_map["ingress"])
    boundary_map["ingress"] = ingress + [
        {
            "name": "bench_ground",
            "kind": "return_path",
            "metered": False,
            "channels": [],
        }
    ]

    findings = validate_energy_paths(
        boundary_map,
        observed_channels=["driver_trace", "load_trace"],
    )

    assert findings == [
        "ingress point 'bench_ground' is unmetered",
        "egress point 'resistor_bank' missing observed channel: resistor_trace_0",
    ]
