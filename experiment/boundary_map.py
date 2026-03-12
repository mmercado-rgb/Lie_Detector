"""Declare and validate energy ingress/egress boundaries for a setup."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast


_BOUNDARY_KEYS = ("setup_id", "ingress", "egress")
_POINT_KEYS = ("name", "kind", "metered", "channels")


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


def _as_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


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


def _direction_label(group_name: str) -> str:
    if group_name == "ingress":
        return "ingress"
    return "egress"


def _normalize_point(point: object, name: str) -> dict[str, object]:
    data = _as_mapping(point, name)
    if set(data.keys()) != set(_POINT_KEYS):
        raise ValueError(f"{name} must contain name, kind, metered, and channels")

    normalized = {
        "name": _as_text(data["name"], f"{name}['name']"),
        "kind": _as_text(data["kind"], f"{name}['kind']"),
        "metered": _as_bool(data["metered"], f"{name}['metered']"),
        "channels": _as_text_list(data["channels"], f"{name}['channels']"),
    }
    if normalized["metered"] and not normalized["channels"]:
        raise ValueError(f"{name} metered points must declare at least one channel")
    return normalized


def _normalize_points(points: object, name: str) -> list[dict[str, object]]:
    if isinstance(points, (str, bytes, bytearray)):
        raise ValueError(f"{name} must be a non-string iterable")
    try:
        raw_points = list(cast(Iterable[object], points))
    except TypeError as exc:
        raise ValueError(f"{name} must be a non-string iterable") from exc
    if not raw_points:
        raise ValueError(f"{name} must not be empty")
    return [
        _normalize_point(point, f"{name}[{index}]")
        for index, point in enumerate(raw_points)
    ]


def normalize_boundary_map(boundary_map: object) -> dict[str, object]:
    """Validate and normalize the explicit energy boundary declaration."""
    data = _as_mapping(boundary_map, "boundary_map")
    if set(data.keys()) != set(_BOUNDARY_KEYS):
        raise ValueError("boundary_map must contain setup_id, ingress, and egress")

    normalized = {
        "setup_id": _as_text(data["setup_id"], "boundary_map['setup_id']"),
        "ingress": _normalize_points(data["ingress"], "boundary_map['ingress']"),
        "egress": _normalize_points(data["egress"], "boundary_map['egress']"),
    }

    seen_names: set[str] = set()
    for group_name in ("ingress", "egress"):
        for point in cast(list[dict[str, object]], normalized[group_name]):
            point_name = cast(str, point["name"])
            if point_name in seen_names:
                raise ValueError("boundary point names must be unique across ingress and egress")
            seen_names.add(point_name)
    return normalized


def build_boundary_registry(boundary_map: object) -> dict[str, dict[str, object]]:
    """Return a point-name keyed registry for deterministic boundary lookups."""
    normalized = normalize_boundary_map(boundary_map)
    registry: dict[str, dict[str, object]] = {}
    for group_name in ("ingress", "egress"):
        for point in cast(list[dict[str, object]], normalized[group_name]):
            registry[cast(str, point["name"])] = {
                "direction": _direction_label(group_name),
                "kind": cast(str, point["kind"]),
                "metered": cast(bool, point["metered"]),
                "channels": list(cast(list[str], point["channels"])),
            }
    return registry


def validate_energy_paths(
    boundary_map: object,
    observed_channels: Iterable[str] | None = None,
) -> list[str]:
    """Return boundary validation findings for missing instrumentation coverage."""
    normalized = normalize_boundary_map(boundary_map)
    observed: set[str] | None = None
    if observed_channels is not None:
        observed = set(_as_text_list(list(observed_channels), "observed_channels"))

    findings: list[str] = []
    for group_name in ("ingress", "egress"):
        direction = _direction_label(group_name)
        for point in cast(list[dict[str, object]], normalized[group_name]):
            point_name = cast(str, point["name"])
            point_channels = cast(list[str], point["channels"])
            if not cast(bool, point["metered"]):
                findings.append(f"{direction} point '{point_name}' is unmetered")
                continue
            if observed is None:
                continue
            for channel_name in point_channels:
                if channel_name not in observed:
                    findings.append(
                        f"{direction} point '{point_name}' missing observed channel: {channel_name}"
                    )
    return findings
