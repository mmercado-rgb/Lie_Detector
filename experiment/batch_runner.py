"""Execute deterministic run data through the accounting pipeline."""

from __future__ import annotations

from collections.abc import Iterable

from experiment.energy_ledger import classify_run, compute_residual
from experiment.results_schema import ResultRecord, make_result_record
from experiment.run_to_ledger import build_ledger


def run_batch(run_data_list: Iterable[object], tau: float) -> list[ResultRecord]:
    results: list[ResultRecord] = []
    for run_data in run_data_list:
        ledger = build_ledger(run_data)
        result = {
            "ledger": ledger,
            "residual": compute_residual(ledger),
            "label": classify_run(ledger, tau),
        }
        results.append(make_result_record(result))
    return results
