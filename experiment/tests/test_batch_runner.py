from __future__ import annotations

import pytest

from experiment.analyze_runs import summarize_results
from experiment.batch_runner import run_batch
from experiment.simulation_variants import (
    make_apparent_excess_run_data,
    make_closed_run_data,
    make_underaccounted_run_data,
)


def test_run_batch_returns_normalized_results() -> None:
    results = run_batch(
        [
            make_closed_run_data(),
            make_underaccounted_run_data(),
            make_apparent_excess_run_data(),
        ],
        1e-9,
    )

    assert len(results) == 3
    assert [result["label"] for result in results] == [
        "CLOSED",
        "UNDERACCOUNTED",
        "APPARENT_EXCESS",
    ]
    assert [result["residual"] for result in results] == pytest.approx([0.0, 1.0, -1.0])
    assert all(list(result.keys()) == ["ledger", "residual", "label"] for result in results)


def test_summarize_results_reports_counts_and_residual_stats() -> None:
    results = run_batch(
        [
            make_closed_run_data(),
            make_underaccounted_run_data(),
            make_apparent_excess_run_data(),
        ],
        1e-9,
    )

    summary = summarize_results(results)

    assert summary == {
        "total_runs": 3,
        "count_closed": 1,
        "count_underaccounted": 1,
        "count_apparent_excess": 1,
        "min_residual": -1.0,
        "max_residual": 1.0,
        "mean_residual": 0.0,
    }
