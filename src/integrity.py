from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast


from src.contract_model import (
    Contract,
    extract_python_script_path,
    load_contract,
    normalize_relative_text,
    require_non_empty_string,
    split_command_tokens,
)
from src.evidence import ensure_within, sha256_file

REPO_CONTRACT_NAME: Final[str] = "workspace.success.yaml"
LOCK_RELATIVE_PATH: Final[str] = ".truth/lock.json"
REQUIRED_LOCKED_FILES: Final[frozenset[str]] = frozenset(
    {
        REPO_CONTRACT_NAME,
        "scripts/preflight.py",
        "scripts/run_agent.py",
        "scripts/verify.py",
        "src/contract_model.py",
    }
)
REQUIRED_COMMAND_RESOLUTIONS: Final[frozenset[str]] = frozenset({"git"})


@dataclass(frozen=True)
class LockedVerifierRun:
    command: str
    probe_path: str


@dataclass(frozen=True)
class LockedCommandResolution:
    policy: str
    path: str


@dataclass(frozen=True)
class IntegrityLock:
    version: int
    contract_path: str
    tracked_files: dict[str, str]
    verifier_runs: dict[str, LockedVerifierRun]
    command_resolution: dict[str, LockedCommandResolution]


def require_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    raw_mapping = cast(dict[object, object], value)
    keys = list(raw_mapping.keys())
    if not all(isinstance(key, str) for key in keys):
        raise ValueError(f"{name} must use string keys")
    return cast(Mapping[str, object], raw_mapping)


def require_exact_keys(
    mapping: Mapping[str, object],
    name: str,
    expected_keys: frozenset[str],
) -> None:
    missing = expected_keys - set(mapping)
    unknown = set(mapping) - expected_keys
    if missing:
        raise ValueError(f"{name} missing keys: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"{name} has unknown keys: {', '.join(sorted(unknown))}")


def require_sha256_text(value: object, name: str) -> str:
    text = require_non_empty_string(value, name)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{name} must be a lowercase sha256 hex digest")
    return text


def require_relative_repo_path(value: object, name: str) -> str:
    return normalize_relative_text(require_non_empty_string(value, name), name, allow_glob=False)


def load_integrity_lock(lock_path: Path) -> IntegrityLock:
    if not lock_path.exists():
        raise ValueError(f"integrity lock is missing: {LOCK_RELATIVE_PATH}")
    raw = cast(object, json.loads(lock_path.read_text(encoding="utf-8")))
    data = require_mapping(raw, LOCK_RELATIVE_PATH)
    require_exact_keys(
        data,
        LOCK_RELATIVE_PATH,
        frozenset({"version", "contract_path", "tracked_files", "verifier_runs", "command_resolution"}),
    )

    version = data.get("version")
    if version != 1:
        raise ValueError("integrity lock version must equal 1")

    tracked_files_raw = require_mapping(data.get("tracked_files"), "tracked_files")
    tracked_files: dict[str, str] = {}
    for raw_path, raw_digest in tracked_files_raw.items():
        relative_path = require_relative_repo_path(raw_path, f"tracked_files.{raw_path}")
        if relative_path in tracked_files:
            raise ValueError(f"tracked_files contains duplicate path: {relative_path}")
        tracked_files[relative_path] = require_sha256_text(raw_digest, f"tracked_files.{relative_path}")

    verifier_runs_raw = require_mapping(data.get("verifier_runs"), "verifier_runs")
    verifier_runs: dict[str, LockedVerifierRun] = {}
    for condition_id, raw_value in verifier_runs_raw.items():
        entry = require_mapping(raw_value, f"verifier_runs.{condition_id}")
        require_exact_keys(
            entry,
            f"verifier_runs.{condition_id}",
            frozenset({"command", "probe_path"}),
        )
        verifier_runs[condition_id] = LockedVerifierRun(
            command=require_non_empty_string(entry.get("command"), f"verifier_runs.{condition_id}.command"),
            probe_path=require_relative_repo_path(
                entry.get("probe_path"),
                f"verifier_runs.{condition_id}.probe_path",
            ),
        )

    command_resolution_raw = require_mapping(data.get("command_resolution"), "command_resolution")
    command_resolution: dict[str, LockedCommandResolution] = {}
    for command_name, raw_value in command_resolution_raw.items():
        entry = require_mapping(raw_value, f"command_resolution.{command_name}")
        require_exact_keys(
            entry,
            f"command_resolution.{command_name}",
            frozenset({"policy", "path"}),
        )
        policy = require_non_empty_string(entry.get("policy"), f"command_resolution.{command_name}.policy")
        if policy != "which":
            raise ValueError(f"unsupported command resolution policy for {command_name}")
        command_resolution[command_name] = LockedCommandResolution(
            policy=policy,
            path=require_non_empty_string(entry.get("path"), f"command_resolution.{command_name}.path"),
        )

    contract_path = require_relative_repo_path(data.get("contract_path"), "contract_path")
    if contract_path != REPO_CONTRACT_NAME:
        raise ValueError(f"contract_path must equal {REPO_CONTRACT_NAME}")

    return IntegrityLock(
        version=1,
        contract_path=contract_path,
        tracked_files=tracked_files,
        verifier_runs=verifier_runs,
        command_resolution=command_resolution,
    )


def load_contract_with_integrity_gate(contract_path: Path) -> Contract:
    return load_contract(contract_path)


def resolve_repo_contract_path(argv: list[str], repo_root: Path) -> Path:
    if len(argv) != 2:
        raise ValueError("entry path requires the repo-root workspace.success.yaml argument")
    expected = ensure_within(repo_root, repo_root / REPO_CONTRACT_NAME, name="repo contract")
    provided = Path(argv[1])
    resolved_provided = provided.resolve() if provided.is_absolute() else (Path.cwd() / provided).resolve()
    if resolved_provided != expected:
        raise ValueError("entry path must use the repo-root workspace.success.yaml")
    if not expected.exists():
        raise ValueError("repo-root workspace.success.yaml is missing")
    return expected


def assert_git_tracked(repo_root: Path, relative_path: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", "--", relative_path],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"integrity lock references a non-git-tracked file: {relative_path}")


def resolve_command_path(command_name: str) -> str:
    resolved = shutil.which(command_name)
    if resolved is None:
        raise ValueError(f"unable to resolve critical command: {command_name}")
    return str(Path(resolved).resolve())


def validate_lock_binding(repo_root: Path, contract: Contract, lock: IntegrityLock) -> None:
    missing_locked_files = REQUIRED_LOCKED_FILES - set(lock.tracked_files)
    if missing_locked_files:
        raise ValueError(
            f"integrity lock missing required tracked files: {', '.join(sorted(missing_locked_files))}"
        )

    assert_git_tracked(repo_root, LOCK_RELATIVE_PATH)

    for relative_path, expected_hash in lock.tracked_files.items():
        assert_git_tracked(repo_root, relative_path)
        absolute_path = ensure_within(repo_root, repo_root / relative_path, name=relative_path)
        if not absolute_path.exists():
            raise ValueError(f"locked file is missing: {relative_path}")
        actual_hash = sha256_file(absolute_path)
        if actual_hash != expected_hash:
            raise ValueError(f"integrity hash mismatch for {relative_path}")

    verifier_conditions = {
        condition.id: condition for condition in contract.success_conditions if condition.is_verifier_run()
    }
    if set(verifier_conditions) != set(lock.verifier_runs):
        missing = set(verifier_conditions) - set(lock.verifier_runs)
        extra = set(lock.verifier_runs) - set(verifier_conditions)
        if missing:
            raise ValueError(
                f"integrity lock missing verifier-run bindings: {', '.join(sorted(missing))}"
            )
        raise ValueError(
            f"integrity lock has undeclared verifier-run bindings: {', '.join(sorted(extra))}"
        )

    for condition_id, condition in verifier_conditions.items():
        locked_run = lock.verifier_runs[condition_id]
        if condition.require_command() != locked_run.command:
            raise ValueError(f"locked verifier command mismatch for {condition_id}")
        probe_path = extract_python_script_path(
            condition.require_command(),
            f"success_conditions.{condition_id}.command",
        )
        if probe_path != locked_run.probe_path:
            raise ValueError(f"locked probe path mismatch for {condition_id}")
        if probe_path not in lock.tracked_files:
            raise ValueError(f"probe file is not hash-locked for {condition_id}")
        _ = ensure_within(repo_root, repo_root / probe_path, name=f"{condition_id}.probe_path")
        assert_git_tracked(repo_root, probe_path)

    required_commands = set(REQUIRED_COMMAND_RESOLUTIONS)
    for condition in contract.success_conditions:
        if not condition.is_command_condition():
            continue
        command_name = split_command_tokens(condition.require_command(), f"success_conditions.{condition.id}.command")[0]
        required_commands.add(Path(command_name).name.lower())

    missing_command_resolutions = required_commands - set(lock.command_resolution)
    if missing_command_resolutions:
        raise ValueError(
            "integrity lock missing command resolutions: "
            + ", ".join(sorted(missing_command_resolutions))
        )

    for command_name in required_commands:
        expected = lock.command_resolution[command_name]
        actual_path = resolve_command_path(command_name)
        if actual_path != expected.path:
            raise ValueError(f"command resolution drift for {command_name}")
