from __future__ import annotations

import re
from pathlib import Path

from src.evidence import ensure_within


RUN_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def parse_run_id(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    run_id = value.strip()
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise ValueError(f"{name} must be a 32-char lowercase hex string")
    return run_id


def resolve_freshness_path(repo_root: Path, freshness_path_text: str) -> Path:
    return ensure_within(repo_root, repo_root / freshness_path_text, name="evidence.freshness_path")


def load_latest_verified_run_id(repo_root: Path, freshness_path_text: str) -> str | None:
    freshness_path = resolve_freshness_path(repo_root, freshness_path_text)
    if not freshness_path.exists():
        return None
    try:
        return parse_run_id(freshness_path.read_text(encoding="utf-8").strip(), "continuity state")
    except ValueError as exc:
        raise ValueError("continuity state is malformed") from exc


def write_latest_verified_run_id(repo_root: Path, freshness_path_text: str, run_id: str) -> None:
    freshness_path = resolve_freshness_path(repo_root, freshness_path_text)
    freshness_path.parent.mkdir(parents=True, exist_ok=True)
    validated_run_id = parse_run_id(run_id, "latest verified run_id")
    _ = freshness_path.write_text(f"{validated_run_id}\n", encoding="utf-8")
