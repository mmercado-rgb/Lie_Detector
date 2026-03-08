from __future__ import annotations

import hashlib
import re
from pathlib import Path


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(payload: str) -> str:
    return sha256_bytes(payload.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def ensure_within(base_dir: Path, candidate: Path, *, name: str) -> Path:
    resolved_base = base_dir.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_base)
    except ValueError as exc:
        raise ValueError(f"{name} must stay within {resolved_base}") from exc
    return resolved_candidate


def ensure_relative_artifact_path(base_dir: Path, relative_name: str, *, name: str) -> Path:
    if not relative_name.strip():
        raise ValueError(f"{name} must be non-empty")
    if "\n" in relative_name or "\r" in relative_name:
        raise ValueError(f"{name} must be single-line")
    return ensure_within(base_dir, base_dir / relative_name, name=name)


def contains_reserved_word(text: str, reserved_words: list[str]) -> str | None:
    lowered_text = text.lower()
    for word in reserved_words:
        pattern = re.compile(rf"(?<![a-z0-9-]){re.escape(word.lower())}(?![a-z0-9-])")
        if pattern.search(lowered_text):
            return word
    return None
