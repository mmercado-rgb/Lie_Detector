from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from src.contract_model import (
    Contract,
    assert_schema_condition_alignment,
    extract_python_script_path,
    validate_contract,
    normalize_relative_text,
    require_non_empty_string,
    split_command_tokens,
)
from src.evidence import ensure_within, sha256_file

REPO_CONTRACT_NAME: Final[str] = "workspace.success.json"
LOCK_RELATIVE_PATH: Final[str] = ".truth/lock.json"
CONTRACT_SCHEMA_RELATIVE_PATH: Final[str] = "schemas/workspace_success.schema.json"
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
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

def _reject_duplicate_mapping_keys(pairs: list[tuple[object, object]]) -> dict[str, object]:
    mapping: dict[str, object] = {}
    for raw_key, value in pairs:
        if not isinstance(raw_key, str):
            raise ValueError("contract json object keys must be strings")
        if raw_key in mapping:
            raise ValueError(f"duplicate mapping key: {raw_key}")
        mapping[raw_key] = value
    return mapping


def parse_contract_json(contract_path: Path) -> object:
    try:
        text = contract_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"contract file not found: {contract_path}") from exc

    try:
        return cast(object, json.loads(text, object_pairs_hook=_reject_duplicate_mapping_keys))
    except json.JSONDecodeError as exc:
        raise ValueError(f"contract json parse error: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"contract json parse error: {exc}") from exc


PathSegment = str | int


def _path_text(path: tuple[PathSegment, ...]) -> str:
    if not path:
        return "contract"
    rendered = "contract"
    for segment in path:
        if isinstance(segment, int):
            rendered += f"[{segment}]"
        else:
            rendered += f".{segment}"
    return rendered


def _type_matches(expected_type: str, value: object) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected_type == "null":
        return value is None
    raise ValueError(f"unsupported schema type: {expected_type}")


def validate_with_schema(schema: object, value: object, path: tuple[PathSegment, ...] = ()) -> None:
    schema_map = require_mapping(schema, f"schema({_path_text(path)})")

    if "oneOf" in schema_map:
        raw_variants = schema_map.get("oneOf")
        if not isinstance(raw_variants, list) or not raw_variants:
            raise ValueError(f"invalid schema at {_path_text(path)}.oneOf")
        matches = 0
        for variant in raw_variants:
            try:
                validate_with_schema(variant, value, path)
                matches += 1
            except ValueError:
                pass
        if matches != 1:
            raise ValueError(f"contract schema validation failed: {_path_text(path)} failed oneOf")
        return

    raw_type = schema_map.get("type")
    if isinstance(raw_type, str):
        if not _type_matches(raw_type, value):
            raise ValueError(f"contract schema validation failed: {_path_text(path)} has invalid type")
    elif isinstance(raw_type, list):
        if not any(isinstance(entry, str) and _type_matches(entry, value) for entry in raw_type):
            raise ValueError(f"contract schema validation failed: {_path_text(path)} has invalid type")

    if "const" in schema_map and value != schema_map.get("const"):
        raise ValueError(f"contract schema validation failed: {_path_text(path)} must equal {schema_map.get('const')!r}")

    raw_enum = schema_map.get("enum")
    if isinstance(raw_enum, list) and value not in raw_enum:
        raise ValueError(f"contract schema validation failed: {_path_text(path)} must be one of enum values")

    if isinstance(value, str):
        raw_min_length = schema_map.get("minLength")
        if isinstance(raw_min_length, int) and len(value) < raw_min_length:
            raise ValueError(
                f"contract schema validation failed: {_path_text(path)} must have minLength {raw_min_length}"
            )
        raw_pattern = schema_map.get("pattern")
        if isinstance(raw_pattern, str) and re.fullmatch(raw_pattern, value) is None:
            raise ValueError(f"contract schema validation failed: {_path_text(path)} failed pattern check")

    if isinstance(value, list):
        raw_min_items = schema_map.get("minItems")
        if isinstance(raw_min_items, int) and len(value) < raw_min_items:
            raise ValueError(
                f"contract schema validation failed: {_path_text(path)} must have minItems {raw_min_items}"
            )
        item_schema = schema_map.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                validate_with_schema(item_schema, item, (*path, index))

    if isinstance(value, dict):
        raw_required = schema_map.get("required")
        if isinstance(raw_required, list):
            missing = [key for key in raw_required if isinstance(key, str) and key not in value]
            if missing:
                raise ValueError(
                    f"contract schema validation failed: {_path_text(path)} missing keys: {', '.join(sorted(missing))}"
                )
        raw_properties = schema_map.get("properties")
        properties: Mapping[str, object] = {}
        if isinstance(raw_properties, dict):
            properties = cast(Mapping[str, object], raw_properties)
            for key, prop_schema in properties.items():
                if key in value:
                    validate_with_schema(prop_schema, value[key], (*path, key))

        if schema_map.get("additionalProperties") is False:
            unknown = set(value) - set(properties)
            if unknown:
                raise ValueError(
                    f"contract schema validation failed: {_path_text(path)} has unknown keys: "
                    + ", ".join(sorted(unknown))
                )


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
    schema_path = PROJECT_ROOT / CONTRACT_SCHEMA_RELATIVE_PATH
    try:
        schema = cast(object, json.loads(schema_path.read_text(encoding="utf-8")))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"failed to load contract schema: {CONTRACT_SCHEMA_RELATIVE_PATH}") from exc
    assert_schema_condition_alignment(schema)

    raw_contract = parse_contract_json(contract_path)
    validate_with_schema(schema, raw_contract)

    return validate_contract(raw_contract)


def resolve_repo_contract_path(argv: list[str], repo_root: Path) -> Path:
    if len(argv) != 2:
        raise ValueError("entry path requires the repo-root workspace.success.json argument")
    expected = ensure_within(repo_root, repo_root / REPO_CONTRACT_NAME, name="repo contract")
    provided = Path(argv[1])
    resolved_provided = provided.resolve() if provided.is_absolute() else (Path.cwd() / provided).resolve()
    if resolved_provided != expected:
        raise ValueError("entry path must use the repo-root workspace.success.json")
    if not expected.exists():
        raise ValueError("repo-root workspace.success.json is missing")
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
