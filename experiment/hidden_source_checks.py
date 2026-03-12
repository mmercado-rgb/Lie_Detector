"""Rule-based checks for hidden sources and boundary violations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast

try:
    from experiment.boundary_map import build_boundary_registry, normalize_boundary_map, validate_energy_paths
except ModuleNotFoundError:  # pragma: no cover - direct script import fallback
    from boundary_map import build_boundary_registry, normalize_boundary_map, validate_energy_paths


_KNOWN_ARTIFACT_FLAGS = (
    "aliasing",
    "phase_misalignment",
    "dc_offset",
    "missed_recharge_window",
    "hidden_ground_return",
    "capacitor_precharge",
    "thermal_lag",
)


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


def _as_text_list(value: object, name: str) -> list[str]:
    if isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{name} must be a non-string iterable")
    try:
        items = list(cast(Iterable[object], value))
    except TypeError as exc:
        raise ValueError(f"{name} must be a non-string iterable") from exc

    normalized: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        text = _as_text(item, f"{name}[{index}]")
        if text in seen:
            raise ValueError(f"{name} must not contain duplicates")
        normalized.append(text)
        seen.add(text)
    return normalized


def normalize_hidden_source_observations(observations: object | None) -> dict[str, object]:
    """Validate normalized artifact observations used for challenge checks."""
    if observations is None:
        return {
            "artifact_flags": [],
            "suspected_sources": [],
            "boundary_violations": [],
            "notes": "",
        }

    data = _as_mapping(observations, "observations")
    allowed_keys = {"artifact_flags", "suspected_sources", "boundary_violations", "notes"}
    if set(data.keys()) - allowed_keys:
        raise ValueError("observations contains unknown keys")

    artifact_flags = _as_text_list(data.get("artifact_flags", []), "observations['artifact_flags']")
    for flag in artifact_flags:
        if flag not in _KNOWN_ARTIFACT_FLAGS:
            raise ValueError(f"observations['artifact_flags'] has unknown flag: {flag}")

    notes = data.get("notes", "")
    if not isinstance(notes, str):
        raise ValueError("observations['notes'] must be a string")

    return {
        "artifact_flags": artifact_flags,
        "suspected_sources": _as_text_list(
            data.get("suspected_sources", []),
            "observations['suspected_sources']",
        ),
        "boundary_violations": _as_text_list(
            data.get("boundary_violations", []),
            "observations['boundary_violations']",
        ),
        "notes": notes.strip(),
    }


def run_hidden_source_checks(
    boundary_map: object,
    observations: object | None = None,
    observed_channels: Iterable[str] | None = None,
) -> dict[str, object]:
    """Return deterministic findings for hidden-source and boundary-map checks."""
    normalized_map = normalize_boundary_map(boundary_map)
    normalized_observations = normalize_hidden_source_observations(observations)
    registry = build_boundary_registry(normalized_map)

    findings = validate_energy_paths(normalized_map, observed_channels=observed_channels)
    for source_name in cast(list[str], normalized_observations["suspected_sources"]):
        findings.append(f"suspected hidden source: {source_name}")
    for violation in cast(list[str], normalized_observations["boundary_violations"]):
        findings.append(f"boundary violation: {violation}")
    for flag in cast(list[str], normalized_observations["artifact_flags"]):
        findings.append(f"artifact challenge failed: {flag}")

    return {
        "passed": not findings,
        "boundary_registry": registry,
        "artifact_flags": list(cast(list[str], normalized_observations["artifact_flags"])),
        "suspected_sources": list(cast(list[str], normalized_observations["suspected_sources"])),
        "boundary_violations": list(cast(list[str], normalized_observations["boundary_violations"])),
        "reasons": findings,
    }
