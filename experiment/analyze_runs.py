"""Summarize normalized deterministic run results."""

from __future__ import annotations

from collections.abc import Iterable

from experiment.results_schema import make_result_record


def summarize_results(results: Iterable[object]) -> dict[str, float | int | None]:
    residuals: list[float] = []
    total_runs = 0
    count_closed = 0
    count_underaccounted = 0
    count_apparent_excess = 0

    for result in results:
        record = make_result_record(result)
        residual = record["residual"]
        residuals.append(residual)
        total_runs += 1
        if record["label"] == "CLOSED":
            count_closed += 1
        elif record["label"] == "UNDERACCOUNTED":
            count_underaccounted += 1
        else:
            count_apparent_excess += 1

    summary: dict[str, float | int | None] = {
        "total_runs": total_runs,
        "count_closed": count_closed,
        "count_underaccounted": count_underaccounted,
        "count_apparent_excess": count_apparent_excess,
        "min_residual": None,
        "max_residual": None,
        "mean_residual": None,
    }
    if residuals:
        summary["min_residual"] = min(residuals)
        summary["max_residual"] = max(residuals)
        summary["mean_residual"] = sum(residuals) / len(residuals)

    return summary
