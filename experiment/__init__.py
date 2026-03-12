"""Public experiment package API for the deterministic ledger pipeline."""

from experiment.analyze_runs import summarize_results
from experiment.batch_runner import run_batch
from experiment.energy_ledger import classify_run, compute_residual, compute_stored_energy, integrate_power
from experiment.results_schema import ResultLabel, ResultRecord, make_result_record
from experiment.run_to_ledger import build_ledger
from experiment.simulation_stub import make_closed_run_data as make_stub_closed_run_data
from experiment.simulation_variants import (
    make_apparent_excess_run_data,
    make_closed_run_data,
    make_underaccounted_run_data,
)

__all__ = [
    "ResultLabel",
    "ResultRecord",
    "build_ledger",
    "classify_run",
    "compute_residual",
    "compute_stored_energy",
    "integrate_power",
    "make_apparent_excess_run_data",
    "make_closed_run_data",
    "make_result_record",
    "make_stub_closed_run_data",
    "make_underaccounted_run_data",
    "run_batch",
    "summarize_results",
]
