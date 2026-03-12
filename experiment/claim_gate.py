"""Gate apparent-excess claims on evidence completeness."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast

from experiment.boundary_map import normalize_boundary_map
from experiment.cross_checks import evaluate_cross_checks
from experiment.hidden_source_checks import run_hidden_source_checks
from experiment.results_schema import make_result_record
from experiment.run_metadata import normalize_run_metadata
from experiment.uncertainty_budget import missing_uncertainty_channels, normalize_uncertainty_budget


_TRACEABILITY_FILES = ("metadata", "raw_traces", "normalized_traces", "ledger", "result")


def _as_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return cast(Mapping[str, object], value)


def _as_text(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _normalize_traceability(traceability: object) -> dict[str, object]:
    data = _as_mapping(traceability, "traceability")
    if set(data.keys()) != {"run_id", "files"}:
        raise ValueError("traceability must contain run_id and files")

    files = _as_mapping(data["files"], "traceability['files']")
    for key in _TRACEABILITY_FILES:
        if key not in files:
            raise ValueError(f"traceability['files'] missing key: {key}")

    return {
        "run_id": _as_text(data["run_id"], "traceability['run_id']"),
        "files": {
            key: _as_text(files[key], f"traceability['files']['{key}']")
            for key in files
        },
    }


def assess_claim(
    result: object,
    metadata: object | None = None,
    uncertainty_budget: object | None = None,
    traceability: object | None = None,
    required_channels: Iterable[str] | None = None,
    boundary_map: object | None = None,
    hidden_source_observations: object | None = None,
    cross_check_data: object | None = None,
) -> dict[str, object]:
    """Return an evidence-aware claim decision without changing ledger math."""
    record = make_result_record(result)
    baseline_label = cast(str, record["label"])

    if baseline_label != "APPARENT_EXCESS":
        return {
            "baseline_label": baseline_label,
            "evidence_label": baseline_label,
            "promotion_state": "NOT_APPLICABLE",
            "promotable": False,
            "traceable": False,
            "required_channels": [],
            "reasons": [],
        }

    reasons: list[str] = []
    normalized_metadata: dict[str, object] | None = None
    normalized_budget: Mapping[str, object] | None = None
    normalized_traceability: dict[str, object] | None = None

    if metadata is None:
        reasons.append("run metadata is required for apparent excess promotion")
    else:
        try:
            normalized_metadata = normalize_run_metadata(metadata)
        except ValueError as exc:
            reasons.append(str(exc))

    if uncertainty_budget is None:
        reasons.append("uncertainty budget is required for apparent excess promotion")
    else:
        try:
            normalized_budget = normalize_uncertainty_budget(uncertainty_budget)
        except ValueError as exc:
            reasons.append(str(exc))

    if traceability is None:
        reasons.append("traceability manifest is required for apparent excess promotion")
    else:
        try:
            normalized_traceability = _normalize_traceability(traceability)
        except ValueError as exc:
            reasons.append(str(exc))

    if required_channels is None and normalized_metadata is not None:
        required_channel_list = list(cast(Mapping[str, object], normalized_metadata["sample_rates"]).keys())
    else:
        required_channel_list = list(required_channels or [])

    if normalized_budget is not None and required_channel_list:
        for channel_name in missing_uncertainty_channels(normalized_budget, required_channel_list):
            reasons.append(f"uncertainty budget missing channel: {channel_name}")

    normalized_boundary_map: dict[str, object] | None = None
    if boundary_map is None:
        reasons.append("boundary map is required for apparent excess promotion")
    else:
        try:
            normalized_boundary_map = normalize_boundary_map(boundary_map)
        except ValueError as exc:
            reasons.append(str(exc))

    if normalized_boundary_map is not None:
        hidden_source_result = run_hidden_source_checks(
            normalized_boundary_map,
            observations=hidden_source_observations,
            observed_channels=required_channel_list,
        )
        reasons.extend(cast(list[str], hidden_source_result["reasons"]))

    if cross_check_data is not None:
        try:
            cross_check_result = evaluate_cross_checks(record["ledger"], cross_check_data)
        except ValueError as exc:
            reasons.append(str(exc))
        else:
            reasons.extend(cast(list[str], cross_check_result["reasons"]))

    traceable = normalized_metadata is not None and normalized_traceability is not None
    if reasons:
        return {
            "baseline_label": baseline_label,
            "evidence_label": "INSUFFICIENT_EVIDENCE",
            "promotion_state": "BLOCKED",
            "promotable": False,
            "traceable": traceable,
            "required_channels": required_channel_list,
            "reasons": reasons,
        }

    return {
        "baseline_label": baseline_label,
        "evidence_label": "APPARENT_EXCESS",
        "promotion_state": "PROMOTABLE",
        "promotable": True,
        "traceable": True,
        "required_channels": required_channel_list,
        "reasons": [],
    }
