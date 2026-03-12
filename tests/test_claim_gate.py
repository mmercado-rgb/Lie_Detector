from __future__ import annotations

from typing import cast

from experiment.claim_gate import assess_claim
from experiment.dataset_storage import write_run_dataset
from experiment.measurement_adapter import normalize_measurement_bundle
from experiment.run_metadata import normalize_run_metadata
from experiment.simulation_variants import make_apparent_excess_run_data, make_closed_run_data
from experiment.batch_runner import run_batch


def _metadata() -> dict[str, object]:
    return {
        "device_ids": {"scope": "SCOPE-01", "probe": "HV-07"},
        "operator": "Ada Lovelace",
        "timestamp": "2026-03-11T16:45:00Z",
        "calibration_ids": {"scope": "CAL-2026-001", "probe": "CAL-2026-002"},
        "ambient_conditions": {"temperature_c": 22.5, "humidity_pct": 41.0},
        "sample_rates": {
            "driver_trace": 1000000.0,
            "load_trace": 1000000.0,
            "resistor_trace_0": 1000000.0,
        },
        "comments": "bench run",
    }


def _uncertainty_budget() -> dict[str, object]:
    return {
        "channels": {
            "driver_trace": {
                "gain": 0.01,
                "offset": 0.001,
                "timing": 1e-9,
                "phase": 0.05,
                "bandwidth": 1000.0,
            },
            "load_trace": {
                "gain": 0.01,
                "offset": 0.001,
                "timing": 1e-9,
                "phase": 0.05,
                "bandwidth": 1000.0,
            },
            "resistor_trace_0": {
                "gain": 0.01,
                "offset": 0.001,
                "timing": 1e-9,
                "phase": 0.05,
                "bandwidth": 1000.0,
            },
        }
    }


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


def _raw_measurements() -> dict[str, object]:
    return {
        "driver_trace": {
            "channel_id": "driver_trace",
            "time_s": [0.0, 1.0],
            "voltage_v": [5.0, 5.0],
            "current_a": [1.0, 1.0],
        },
        "load_trace": {
            "channel_id": "load_trace",
            "time_s": [0.0, 1.0],
            "voltage_v": [4.0, 4.0],
            "current_a": [1.0, 1.0],
        },
        "resistor_traces": [
            {
                "channel_id": "resistor_trace_0",
                "time_s": [0.0, 1.0],
                "voltage_v": [1.0, 1.0],
                "current_a": [1.0, 1.0],
            }
        ],
    }


def test_assess_claim_downgrades_apparent_excess_without_evidence() -> None:
    result = run_batch([make_apparent_excess_run_data()], tau=1e-9)[0]

    assessment = assess_claim(result)

    assert assessment["baseline_label"] == "APPARENT_EXCESS"
    assert assessment["evidence_label"] == "INSUFFICIENT_EVIDENCE"
    assert assessment["promotion_state"] == "BLOCKED"
    assert assessment["promotable"] is False
    assert assessment["reasons"]


def test_assess_claim_promotes_traceable_apparent_excess(tmp_path) -> None:
    result = run_batch([make_apparent_excess_run_data()], tau=1e-9)[0]
    metadata = _metadata()
    raw_measurements = _raw_measurements()
    normalized_measurements = normalize_measurement_bundle(raw_measurements)
    manifest = write_run_dataset(
        tmp_path,
        metadata=metadata,
        raw_traces=raw_measurements,
        normalized_traces=normalized_measurements,
        result=result,
        uncertainty_budget=_uncertainty_budget(),
    )

    assessment = assess_claim(
        result,
        metadata=metadata,
        uncertainty_budget=_uncertainty_budget(),
        traceability=manifest,
        boundary_map=_boundary_map(),
    )

    assert assessment == {
        "baseline_label": "APPARENT_EXCESS",
        "evidence_label": "APPARENT_EXCESS",
        "promotion_state": "PROMOTABLE",
        "promotable": True,
        "traceable": True,
        "required_channels": ["driver_trace", "load_trace", "resistor_trace_0"],
        "reasons": [],
    }


def test_assess_claim_blocks_apparent_excess_without_boundary_map(tmp_path) -> None:
    result = run_batch([make_apparent_excess_run_data()], tau=1e-9)[0]
    metadata = _metadata()
    raw_measurements = _raw_measurements()
    normalized_measurements = normalize_measurement_bundle(raw_measurements)
    manifest = write_run_dataset(
        tmp_path,
        metadata=metadata,
        raw_traces=raw_measurements,
        normalized_traces=normalized_measurements,
        result=result,
        uncertainty_budget=_uncertainty_budget(),
    )

    assessment = assess_claim(
        result,
        metadata=metadata,
        uncertainty_budget=_uncertainty_budget(),
        traceability=manifest,
    )

    assert assessment["evidence_label"] == "INSUFFICIENT_EVIDENCE"
    assert "boundary map is required for apparent excess promotion" in cast(list[str], assessment["reasons"])


def test_assess_claim_blocks_artifact_challenge_failures(tmp_path) -> None:
    result = run_batch([make_apparent_excess_run_data()], tau=1e-9)[0]
    metadata = _metadata()
    raw_measurements = _raw_measurements()
    normalized_measurements = normalize_measurement_bundle(raw_measurements)
    manifest = write_run_dataset(
        tmp_path,
        metadata=metadata,
        raw_traces=raw_measurements,
        normalized_traces=normalized_measurements,
        result=result,
        uncertainty_budget=_uncertainty_budget(),
    )

    assessment = assess_claim(
        result,
        metadata=metadata,
        uncertainty_budget=_uncertainty_budget(),
        traceability=manifest,
        boundary_map=_boundary_map(),
        hidden_source_observations={"artifact_flags": ["aliasing"]},
        cross_check_data={
            "battery_depletion": {"observed_input_energy": 4.7, "tolerance": 0.05},
        },
    )

    assert assessment["evidence_label"] == "INSUFFICIENT_EVIDENCE"
    assert assessment["promotion_state"] == "BLOCKED"
    assert assessment["promotable"] is False
    assert assessment["reasons"] == [
        "artifact challenge failed: aliasing",
        "battery depletion disagrees with electrical driver energy",
    ]


def test_assess_claim_leaves_non_apparent_results_unchanged() -> None:
    result = run_batch([make_closed_run_data()], tau=1e-9)[0]

    assessment = assess_claim(result, metadata=normalize_run_metadata(_metadata()))

    assert assessment["baseline_label"] == "CLOSED"
    assert assessment["evidence_label"] == "CLOSED"
    assert assessment["promotion_state"] == "NOT_APPLICABLE"
