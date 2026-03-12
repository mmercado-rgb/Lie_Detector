"""Represent deterministic per-channel uncertainty budgets."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast


_UNCERTAINTY_COMPONENTS = ("gain", "offset", "timing", "phase", "bandwidth")


def _as_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return cast(Mapping[str, object], value)


def _as_float(value: object, name: str) -> float:
    if isinstance(value, bool) or isinstance(value, (bytes, bytearray)):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(cast(int | float | str, value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if number != number or number in (float("inf"), float("-inf")):
        raise ValueError(f"{name} must be finite")
    return number


def normalize_uncertainty_budget(budget: object) -> dict[str, dict[str, dict[str, float]]]:
    """Validate the locked uncertainty schema for all measured channels."""
    data = _as_mapping(budget, "budget")
    if set(data.keys()) != {"channels"}:
        raise ValueError("budget must contain exactly the channels mapping")

    channels = _as_mapping(data["channels"], "budget['channels']")
    if not channels:
        raise ValueError("budget['channels'] must not be empty")

    normalized_channels: dict[str, dict[str, float]] = {}
    for channel_name, terms in channels.items():
        if not isinstance(channel_name, str) or not channel_name.strip():
            raise ValueError("budget['channels'] keys must be non-empty strings")
        term_map = _as_mapping(terms, f"budget['channels']['{channel_name}']")
        if set(term_map.keys()) != set(_UNCERTAINTY_COMPONENTS):
            raise ValueError(
                f"budget['channels']['{channel_name}'] must contain gain, offset, timing, phase, and bandwidth"
            )

        normalized_terms: dict[str, float] = {}
        for component in _UNCERTAINTY_COMPONENTS:
            magnitude = _as_float(
                term_map[component],
                f"budget['channels']['{channel_name}']['{component}']",
            )
            if magnitude < 0.0:
                raise ValueError(
                    f"budget['channels']['{channel_name}']['{component}'] must be >= 0"
                )
            normalized_terms[component] = magnitude
        normalized_channels[channel_name.strip()] = normalized_terms

    return {"channels": normalized_channels}


def missing_uncertainty_channels(budget: object, required_channels: Iterable[str]) -> list[str]:
    """Return required channel names that are absent from the normalized budget."""
    normalized = normalize_uncertainty_budget(budget)
    known_channels = normalized["channels"]
    return [
        channel
        for channel in required_channels
        if channel not in known_channels
    ]
