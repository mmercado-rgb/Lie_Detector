from __future__ import annotations

from experiment import (
    build_ledger,
    make_apparent_excess_run_data,
    make_closed_run_data,
    make_result_record,
    make_underaccounted_run_data,
    run_batch,
    summarize_results,
)


def test_experiment_package_exports_pipeline_api() -> None:
    closed_run = make_closed_run_data()
    underaccounted_run = make_underaccounted_run_data()
    apparent_excess_run = make_apparent_excess_run_data()

    ledger = build_ledger(closed_run)
    result = run_batch([closed_run, underaccounted_run, apparent_excess_run], tau=1e-9)

    assert make_result_record(result[0]) == result[0]
    assert ledger["E_driver"] == 5.0
    assert [item["label"] for item in result] == ["CLOSED", "UNDERACCOUNTED", "APPARENT_EXCESS"]
    assert summarize_results(result) == {
        "total_runs": 3,
        "count_closed": 1,
        "count_underaccounted": 1,
        "count_apparent_excess": 1,
        "min_residual": -1.0,
        "max_residual": 1.0,
        "mean_residual": 0.0,
    }
