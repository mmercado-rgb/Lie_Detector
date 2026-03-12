from __future__ import annotations

import json

from experiment.dataset_storage import write_run_dataset, write_summary
from experiment.measurement_adapter import normalize_measurement_bundle
from experiment.simulation_variants import make_closed_run_data
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
            "voltage_v": [3.0, 3.0],
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


def test_write_run_dataset_uses_deterministic_layout(tmp_path) -> None:
    result = run_batch([make_closed_run_data()], tau=1e-9)[0]
    metadata = _metadata()
    raw_measurements = _raw_measurements()
    normalized_measurements = normalize_measurement_bundle(raw_measurements)

    manifest_one = write_run_dataset(
        tmp_path,
        metadata=metadata,
        raw_traces=raw_measurements,
        normalized_traces=normalized_measurements,
        result=result,
    )
    manifest_two = write_run_dataset(
        tmp_path,
        metadata=metadata,
        raw_traces=raw_measurements,
        normalized_traces=normalized_measurements,
        result=result,
    )

    assert manifest_one == manifest_two
    run_dir = tmp_path / "runs" / manifest_one["run_id"]
    assert (run_dir / "raw_traces.json").is_file()
    assert (run_dir / "normalized_traces.json").is_file()
    assert (run_dir / "ledger.json").is_file()

    ledger_payload = json.loads((run_dir / "ledger.json").read_text(encoding="utf-8"))
    assert ledger_payload == result["ledger"]


def test_write_summary_persists_run_ids(tmp_path) -> None:
    result = run_batch([make_closed_run_data()], tau=1e-9)[0]
    manifest = write_run_dataset(
        tmp_path,
        metadata=_metadata(),
        raw_traces=_raw_measurements(),
        normalized_traces=normalize_measurement_bundle(_raw_measurements()),
        result=result,
    )

    summary_ref = write_summary(
        tmp_path,
        "Bench Summary 2026-03-11",
        {"total_runs": 1},
        [manifest],
    )

    assert summary_ref == {
        "name": "bench_summary_2026_03_11",
        "path": "summaries/bench_summary_2026_03_11.json",
    }
    summary_payload = json.loads(
        (tmp_path / "summaries" / "bench_summary_2026_03_11.json").read_text(encoding="utf-8")
    )
    assert summary_payload["run_ids"] == [manifest["run_id"]]
    assert summary_payload["summary"] == {"total_runs": 1}
