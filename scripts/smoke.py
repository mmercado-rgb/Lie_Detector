from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TAU = 1e-9


def _format_scenario(name: str, residual: float, label: str) -> str:
    return f"{name}: residual={residual}, label={label}"


def main() -> int:
    try:
        from experiment import (
            assess_claim,
            build_boundary_registry,
            build_ledger,
            evaluate_cross_checks,
            get_artifact_scenario,
            classify_run,
            compute_residual,
            compute_stored_energy,
            integrate_power,
            list_artifact_scenarios,
            make_apparent_excess_run_data,
            make_closed_run_data,
            make_result_record,
            make_underaccounted_run_data,
            missing_uncertainty_channels,
            normalize_boundary_map,
            normalize_measurement_bundle,
            normalize_measurement_export,
            normalize_run_metadata,
            normalize_uncertainty_budget,
            run_batch,
            run_hidden_source_checks,
            summarize_results,
            validate_energy_paths,
            write_run_dataset,
            write_summary,
        )

        stored = compute_stored_energy({"L": [1.0], "i_L": [2.0], "C": [1.0], "v_C": [3.0]})
        if abs(stored - 6.5) > TAU:
            raise RuntimeError("compute_stored_energy mismatch")
        print(f"stored_energy_example: {stored}")

        integrated = integrate_power({"v": [1.0, 1.0, 1.0], "i": [2.0, 2.0, 2.0], "t": [0.0, 1.0, 2.0]})
        if abs(integrated - 4.0) > TAU:
            raise RuntimeError("integrate_power mismatch")
        print(f"integrate_power_example: {integrated}")

        scenarios = [
            ("closed_system", make_closed_run_data(), 0.0, "CLOSED"),
            ("underaccounted_energy", make_underaccounted_run_data(), 1.0, "UNDERACCOUNTED"),
            ("apparent_excess_energy", make_apparent_excess_run_data(), -1.0, "APPARENT_EXCESS"),
        ]

        for name, scenario_run_data, expected_residual, expected_label in scenarios:
            ledger = build_ledger(scenario_run_data)
            residual = compute_residual(ledger)
            if abs(residual - expected_residual) > TAU:
                raise RuntimeError(f"{name} residual mismatch")
            label = classify_run(ledger, TAU)
            if label != expected_label:
                raise RuntimeError(f"{name} classification mismatch")
            print(_format_scenario(name, residual, label))

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
        expected_ledger = {
            "E_driver": 5.0,
            "E_load": 3.0,
            "E_R": 1.0,
            "E_rad": 0.5,
            "E_parasitic": 0.5,
            "E_stored_t0": 0.0,
            "E_stored_t1": 0.0,
        }
        if list(ledger.keys()) != list(expected_ledger.keys()):
            raise RuntimeError("build_ledger key order mismatch")
        for key, expected_value in expected_ledger.items():
            if abs(ledger[key] - expected_value) > TAU:
                raise RuntimeError(f"build_ledger mismatch for {key}")

        residual = compute_residual(ledger)
        if abs(residual - 0.0) > TAU:
            raise RuntimeError("build_ledger residual mismatch")
        label = classify_run(ledger, TAU)
        if label != "CLOSED":
            raise RuntimeError("build_ledger classification mismatch")
        print(_format_scenario("run_to_ledger_closed", residual, label))

        single_batch = run_batch([make_closed_run_data()], TAU)
        if not isinstance(single_batch, list):
            raise RuntimeError("run_batch did not return list")
        if len(single_batch) != 1:
            raise RuntimeError("run_batch record count mismatch")

        record = single_batch[0]
        if record != make_result_record(record):
            raise RuntimeError("run_batch record shape mismatch")
        if abs(record["residual"] - 0.0) > TAU:
            raise RuntimeError("run_batch residual mismatch")
        if record["label"] != "CLOSED":
            raise RuntimeError("run_batch label mismatch")
        print(f"batch_runner_closed: count={len(single_batch)}, label={record['label']}")

        mixed_batch = run_batch(
            [
                make_closed_run_data(),
                make_underaccounted_run_data(),
                make_apparent_excess_run_data(),
            ],
            TAU,
        )
        if [item["label"] for item in mixed_batch] != ["CLOSED", "UNDERACCOUNTED", "APPARENT_EXCESS"]:
            raise RuntimeError("run_batch mixed classification mismatch")
        print("batch_runner_mixed: labels=CLOSED,UNDERACCOUNTED,APPARENT_EXCESS")

        summary = summarize_results(mixed_batch)
        expected_summary = {
            "total_runs": 3,
            "count_closed": 1,
            "count_underaccounted": 1,
            "count_apparent_excess": 1,
            "min_residual": -1.0,
            "max_residual": 1.0,
            "mean_residual": 0.0,
        }
        if summary != expected_summary:
            raise RuntimeError("summarize_results mismatch")
        print(
            "analyze_runs_mixed: "
            f"total_runs={summary['total_runs']}, "
            f"count_closed={summary['count_closed']}, "
            f"count_underaccounted={summary['count_underaccounted']}, "
            f"count_apparent_excess={summary['count_apparent_excess']}"
        )

        measurement = normalize_measurement_export(
            {
                "trace_id": "driver-v-i",
                "channel_id": "driver_trace",
                "time_s": [0.0, 1.0],
                "voltage_v": [5.0, 5.0],
                "current_a": [1.0, 1.0],
                "sample_rate_hz": "1000000",
            }
        )
        if measurement["trace_id"] != "driver-v-i":
            raise RuntimeError("normalize_measurement_export trace mismatch")
        print(
            "measurement_adapter_example: "
            f"trace_id={measurement['trace_id']}, sample_rate_hz={measurement['sample_rate_hz']}"
        )

        raw_measurements = {
            "driver_trace": {
                "trace_id": "driver-v-i",
                "channel_id": "driver_trace",
                "time_s": [0.0, 1.0],
                "voltage_v": [5.0, 5.0],
                "current_a": [1.0, 1.0],
            },
            "load_trace": {
                "trace_id": "load-v-i",
                "channel_id": "load_trace",
                "time_s": [0.0, 1.0],
                "voltage_v": [4.0, 4.0],
                "current_a": [1.0, 1.0],
            },
            "resistor_traces": [
                {
                    "trace_id": "resistor-v-i",
                    "channel_id": "resistor_trace_0",
                    "time_s": [0.0, 1.0],
                    "voltage_v": [1.0, 1.0],
                    "current_a": [1.0, 1.0],
                }
            ],
        }
        normalized_measurements = normalize_measurement_bundle(raw_measurements)

        metadata = normalize_run_metadata(
            {
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
        )
        print(
            "run_metadata_example: "
            f"operator={metadata['operator']}, timestamp={metadata['timestamp']}"
        )

        uncertainty_budget = normalize_uncertainty_budget(
            {
                "channels": {
                    "driver_trace": {
                        "gain": 0.01,
                        "offset": 0.001,
                        "timing": 1e-9,
                        "phase": 0.05,
                        "bandwidth": 1000.0,
                    }
                }
            }
        )
        missing_channels = missing_uncertainty_channels(
            uncertainty_budget,
            ["driver_trace", "load_trace"],
        )
        if missing_channels != ["load_trace"]:
            raise RuntimeError("missing_uncertainty_channels mismatch")
        print(f"uncertainty_budget_example: missing={missing_channels[0]}")

        boundary_map = normalize_boundary_map(
            {
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
        )
        registry = build_boundary_registry(boundary_map)
        findings = validate_energy_paths(
            boundary_map,
            observed_channels=["driver_trace", "load_trace", "resistor_trace_0"],
        )
        if registry["driver_supply"]["direction"] != "ingress":
            raise RuntimeError("build_boundary_registry mismatch")
        if findings:
            raise RuntimeError("validate_energy_paths mismatch")
        print(
            "boundary_map_example: "
            f"ingress={len(boundary_map['ingress'])}, egress={len(boundary_map['egress'])}, findings={len(findings)}"
        )

        hidden_source_result = run_hidden_source_checks(
            boundary_map,
            observations={"artifact_flags": ["aliasing"]},
            observed_channels=["driver_trace", "load_trace", "resistor_trace_0"],
        )
        if hidden_source_result["passed"]:
            raise RuntimeError("run_hidden_source_checks mismatch")
        print(
            "hidden_source_checks_example: "
            f"passed={hidden_source_result['passed']}, reasons={len(hidden_source_result['reasons'])}"
        )

        cross_check_result = evaluate_cross_checks(
            build_ledger(make_closed_run_data()),
            {
                "battery_depletion": {"observed_input_energy": 5.0, "tolerance": 0.05},
                "calorimetry": {"observed_output_energy": 5.0, "tolerance": 0.05},
            },
        )
        if cross_check_result["status"] != "PASS":
            raise RuntimeError("evaluate_cross_checks mismatch")
        print(
            "cross_checks_example: "
            f"status={cross_check_result['status']}, comparisons={len(cross_check_result['comparisons'])}"
        )

        apparent_result = run_batch([make_apparent_excess_run_data()], TAU)[0]
        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest = write_run_dataset(
                tmp_dir,
                metadata=metadata,
                raw_traces=raw_measurements,
                normalized_traces=normalized_measurements,
                result=apparent_result,
                uncertainty_budget={
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
                },
            )
            summary_ref = write_summary(
                tmp_dir,
                "Bench Summary 2026-03-11",
                {"total_runs": 1},
                [manifest],
            )
        print(
            "dataset_storage_example: "
            f"files={len(manifest['files'])}, summary={summary_ref['path']}"
        )

        claim_assessment = assess_claim(
            apparent_result,
            metadata=metadata,
            uncertainty_budget={
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
            },
            traceability=manifest,
            boundary_map=boundary_map,
        )
        if claim_assessment["promotion_state"] != "PROMOTABLE":
            raise RuntimeError("assess_claim mismatch")
        print(
            "claim_gate_example: "
            f"promotion_state={claim_assessment['promotion_state']}, "
            f"evidence_label={claim_assessment['evidence_label']}"
        )

        scenarios = list_artifact_scenarios()
        aliasing = get_artifact_scenario("aliasing")
        aliasing_result = run_batch([aliasing["run_data"]], TAU)[0]
        if aliasing_result["label"] != "APPARENT_EXCESS":
            raise RuntimeError("artifact_library mismatch")
        print(
            "artifact_library_example: "
            f"scenarios={len(scenarios)}, aliasing_label={aliasing_result['label']}"
        )

        print("smoke_complete")
        return 0

    except Exception as exc:
        print(f"smoke_error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
