from __future__ import annotations

import re
import shlex
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, cast

ConditionType = Literal[
    "command_exit_zero",
    "file_exists",
    "command_stdout_contains",
    "verifier_command_exit_zero",
    "verifier_stdout_contains",
]

EXECUTOR_COMMAND_TYPES: Final[frozenset[ConditionType]] = frozenset(
    {"command_exit_zero", "command_stdout_contains"}
)
VERIFIER_COMMAND_TYPES: Final[frozenset[ConditionType]] = frozenset(
    {"verifier_command_exit_zero", "verifier_stdout_contains"}
)
COMMAND_TYPES: Final[frozenset[ConditionType]] = frozenset(
    (*EXECUTOR_COMMAND_TYPES, *VERIFIER_COMMAND_TYPES)
)
SUPPORTED_TYPES: Final[frozenset[ConditionType]] = frozenset((*COMMAND_TYPES, "file_exists"))
SCHEMA_REQUIRED_CONDITION_FIELDS: Final[dict[ConditionType, frozenset[str]]] = {
    "command_exit_zero": frozenset({"command"}),
    "verifier_command_exit_zero": frozenset({"command"}),
    "command_stdout_contains": frozenset({"command", "contains"}),
    "verifier_stdout_contains": frozenset({"command", "contains"}),
    "file_exists": frozenset({"path"}),
}
REQUIRED_TOP_LEVEL_FIELDS: Final[tuple[str, ...]] = (
    "version",
    "task_id",
    "goal",
    "inputs",
    "success_conditions",
    "evidence",
    "policy",
)
HASH_ALGORITHMS: Final[frozenset[str]] = frozenset({"sha256"})
ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SHELL_REDIRECTION_TOKENS: Final[tuple[str, ...]] = (">", "<", "|", ";", "&&", "||")


@dataclass(frozen=True)
class Inputs:
    repo_root: str
    allowed_paths: list[str]


@dataclass(frozen=True)
class Evidence:
    output_dir: str
    save_stdout: bool
    save_stderr: bool
    save_exit_codes: bool
    hash_algorithm: str
    freshness_path: str


@dataclass(frozen=True)
class Policy:
    fail_closed: bool
    executor_cannot_claim_success: bool
    verifier_is_final_authority: bool
    require_black_box_verification: bool
    reserved_outcome_words: list[str]


@dataclass(frozen=True)
class SuccessCondition:
    id: str
    type: ConditionType
    command: str | None = None
    path: str | None = None
    contains: str | None = None

    def require_command(self) -> str:
        if self.command is None:
            raise ValueError(f"success condition {self.id} requires a command")
        return self.command

    def require_path(self) -> str:
        if self.path is None:
            raise ValueError(f"success condition {self.id} requires a path")
        return self.path

    def require_contains(self) -> str:
        if self.contains is None:
            raise ValueError(f"success condition {self.id} requires a contains value")
        return self.contains

    def is_executor_run(self) -> bool:
        return self.type in EXECUTOR_COMMAND_TYPES

    def is_verifier_run(self) -> bool:
        return self.type in VERIFIER_COMMAND_TYPES

    def is_command_condition(self) -> bool:
        return self.type in COMMAND_TYPES


@dataclass(frozen=True)
class Contract:
    version: int
    task_id: str
    goal: str
    inputs: Inputs
    success_conditions: list[SuccessCondition]
    evidence: Evidence
    policy: Policy


def load_contract(contract_path: Path) -> Contract:
    raise ValueError(
        "direct contract loading is forbidden; use load_contract_with_integrity_gate(contract_path)"
    )


def require_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    raw_mapping = cast(dict[object, object], value)
    keys: list[object] = list(raw_mapping.keys())
    if not all(isinstance(key, str) for key in keys):
        raise ValueError(f"{name} must use string keys")
    return cast(Mapping[str, object], raw_mapping)


def require_non_empty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    stripped = value.strip()
    if "\n" in stripped or "\r" in stripped:
        raise ValueError(f"{name} must be a single-line string")
    return stripped


def require_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def require_non_empty_list(value: object, name: str) -> list[object]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a non-empty list")
    return cast(list[object], value)


def parse_condition_type(value: object, name: str) -> ConditionType:
    type_name = require_non_empty_string(value, name)
    if type_name not in SUPPORTED_TYPES:
        raise ValueError(f"unsupported success condition type: {type_name}")
    return cast(ConditionType, type_name)


def normalize_relative_text(value: str, name: str, allow_glob: bool = False) -> str:
    normalized = value.replace("\\", "/")
    if normalized in {"", ".", "./"}:
        raise ValueError(f"{name} must not be empty or dot-only")
    if Path(normalized).is_absolute() or normalized.startswith("/"):
        raise ValueError(f"{name} must stay within repo scope")
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        raise ValueError(f"{name} must stay within repo scope")
    if not allow_glob and any(token in normalized for token in ("*", "?")):
        raise ValueError(f"{name} must not contain glob tokens")
    return normalized


def require_repo_root(value: object, name: str) -> str:
    text = require_non_empty_string(value, name)
    if text != ".":
        raise ValueError(f"{name} must equal '.'")
    return text


def require_repo_relative_path(value: object, name: str) -> str:
    return normalize_relative_text(require_non_empty_string(value, name), name, allow_glob=False)


def require_repo_relative_pattern(value: object, name: str) -> str:
    return normalize_relative_text(require_non_empty_string(value, name), name, allow_glob=True)


def require_condition_id(value: object, name: str) -> str:
    condition_id = require_non_empty_string(value, name)
    if ID_PATTERN.fullmatch(condition_id) is None:
        raise ValueError(f"{name} must match {ID_PATTERN.pattern}")
    return condition_id


def require_command(value: object, name: str, verifier_run: bool) -> str:
    command = require_non_empty_string(value, name)
    if verifier_run and any(token in command for token in SHELL_REDIRECTION_TOKENS):
        raise ValueError(f"{name} contains unsupported shell control tokens")
    return command


def split_command_tokens(command: str, name: str) -> list[str]:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        raise ValueError(f"{name} is not shell-parseable") from exc
    if not tokens:
        raise ValueError(f"{name} must contain at least one token")
    return tokens


def extract_python_script_path(command: str, name: str) -> str:
    tokens = split_command_tokens(command, name)
    executable_name = Path(tokens[0]).name.lower()
    if executable_name not in {"python", "python.exe"}:
        raise ValueError(f"{name} must invoke a python probe script")
    if len(tokens) < 2 or tokens[1] in {"-c", "-m"}:
        raise ValueError(f"{name} must reference a repo probe script")
    return normalize_relative_text(tokens[1], name, allow_glob=False)


def require_string_list(value: object, name: str) -> list[str]:
    raw_list = require_non_empty_list(value, name)
    parsed = [require_non_empty_string(item, f"{name}[{index}]") for index, item in enumerate(raw_list)]
    if len(set(parsed)) != len(parsed):
        raise ValueError(f"{name} must not contain duplicates")
    return parsed


def parse_inputs(inputs_value: object) -> Inputs:
    inputs = require_mapping(inputs_value, "inputs")
    repo_root = require_repo_root(inputs.get("repo_root"), "inputs.repo_root")
    allowed_paths_value = require_non_empty_list(
        inputs.get("allowed_paths"),
        "inputs.allowed_paths",
    )
    allowed_paths = [
        require_repo_relative_pattern(item, f"inputs.allowed_paths[{index}]")
        for index, item in enumerate(allowed_paths_value)
    ]
    return Inputs(repo_root=repo_root, allowed_paths=allowed_paths)


def parse_evidence(evidence_value: object) -> Evidence:
    evidence = require_mapping(evidence_value, "evidence")
    hash_algorithm = require_non_empty_string(evidence.get("hash_algorithm"), "evidence.hash_algorithm")
    if hash_algorithm not in HASH_ALGORITHMS:
        raise ValueError(f"unsupported evidence.hash_algorithm: {hash_algorithm}")
    return Evidence(
        output_dir=require_repo_relative_path(evidence.get("output_dir"), "evidence.output_dir"),
        save_stdout=require_bool(evidence.get("save_stdout"), "evidence.save_stdout"),
        save_stderr=require_bool(evidence.get("save_stderr"), "evidence.save_stderr"),
        save_exit_codes=require_bool(evidence.get("save_exit_codes"), "evidence.save_exit_codes"),
        hash_algorithm=hash_algorithm,
        freshness_path=require_repo_relative_path(evidence.get("freshness_path"), "evidence.freshness_path"),
    )


def parse_policy(policy_value: object) -> Policy:
    policy = require_mapping(policy_value, "policy")
    return Policy(
        fail_closed=require_bool(policy.get("fail_closed"), "policy.fail_closed"),
        executor_cannot_claim_success=require_bool(
            policy.get("executor_cannot_claim_success"),
            "policy.executor_cannot_claim_success",
        ),
        verifier_is_final_authority=require_bool(
            policy.get("verifier_is_final_authority"),
            "policy.verifier_is_final_authority",
        ),
        require_black_box_verification=require_bool(
            policy.get("require_black_box_verification"),
            "policy.require_black_box_verification",
        ),
        reserved_outcome_words=require_string_list(
            policy.get("reserved_outcome_words"),
            "policy.reserved_outcome_words",
        ),
    )


def parse_success_condition(index: int, item: object) -> SuccessCondition:
    condition = require_mapping(item, f"success_conditions[{index}]")
    condition_type = parse_condition_type(
        condition.get("type"),
        f"success_conditions[{index}].type",
    )
    verifier_run = condition_type in VERIFIER_COMMAND_TYPES
    return SuccessCondition(
        id=require_condition_id(condition.get("id"), f"success_conditions[{index}].id"),
        type=condition_type,
        command=(
            require_command(
                condition.get("command"),
                f"success_conditions[{index}].command",
                verifier_run=verifier_run,
            )
            if condition_type in COMMAND_TYPES
            else None
        ),
        path=(
            require_repo_relative_path(condition.get("path"), f"success_conditions[{index}].path")
            if condition_type == "file_exists"
            else None
        ),
        contains=(
            require_non_empty_string(
                condition.get("contains"),
                f"success_conditions[{index}].contains",
            )
            if condition_type in {"command_stdout_contains", "verifier_stdout_contains"}
            else None
        ),
    )


def parse_success_conditions(conditions_value: object) -> list[SuccessCondition]:
    condition_items = require_non_empty_list(conditions_value, "success_conditions")
    conditions: list[SuccessCondition] = []
    seen_ids: set[str] = set()

    for index, item in enumerate(condition_items):
        parsed = parse_success_condition(index, item)
        if parsed.id in seen_ids:
            raise ValueError(f"duplicate success condition id: {parsed.id}")
        seen_ids.add(parsed.id)
        conditions.append(parsed)

    return conditions


def validate_contract(contract_value: object) -> Contract:
    contract = require_mapping(contract_value, "contract")
    missing_required = [field for field in REQUIRED_TOP_LEVEL_FIELDS if field not in contract]
    if missing_required:
        raise ValueError(f"contract missing keys: {', '.join(sorted(missing_required))}")

    version = contract.get("version")
    if version != 2:
        raise ValueError("version must equal 2")

    parsed_contract = Contract(
        version=2,
        task_id=require_non_empty_string(contract.get("task_id"), "task_id"),
        goal=require_non_empty_string(contract.get("goal"), "goal"),
        inputs=parse_inputs(contract.get("inputs")),
        success_conditions=parse_success_conditions(contract.get("success_conditions")),
        evidence=parse_evidence(contract.get("evidence")),
        policy=parse_policy(contract.get("policy")),
    )

    if parsed_contract.policy.require_black_box_verification and not any(
        condition.is_verifier_run() for condition in parsed_contract.success_conditions
    ):
        raise ValueError("policy.require_black_box_verification requires a verifier-run condition")

    return parsed_contract


def assert_schema_condition_alignment(schema: object) -> None:
    schema_map = require_mapping(schema, "schema")
    properties = require_mapping(schema_map.get("properties"), "schema.properties")
    success_conditions = require_mapping(
        properties.get("success_conditions"),
        "schema.properties.success_conditions",
    )
    items = require_mapping(
        success_conditions.get("items"),
        "schema.properties.success_conditions.items",
    )
    raw_variants = items.get("oneOf")
    if not isinstance(raw_variants, list) or not raw_variants:
        raise ValueError("schema success condition variants are invalid")

    schema_required_fields: dict[ConditionType, frozenset[str]] = {}
    for index, variant in enumerate(raw_variants):
        variant_map = require_mapping(variant, f"schema success condition variant {index}")
        variant_properties = require_mapping(
            variant_map.get("properties"),
            f"schema success condition variant {index}.properties",
        )
        type_schema = require_mapping(
            variant_properties.get("type"),
            f"schema success condition variant {index}.properties.type",
        )
        raw_condition_type = type_schema.get("const")
        if not isinstance(raw_condition_type, str) or raw_condition_type not in SUPPORTED_TYPES:
            raise ValueError(
                f"schema success condition variant {index} has unsupported type const"
            )
        condition_type = cast(ConditionType, raw_condition_type)
        if condition_type in schema_required_fields:
            raise ValueError(f"schema has duplicate success condition type: {condition_type}")

        raw_required = variant_map.get("required")
        if not isinstance(raw_required, list) or not raw_required:
            raise ValueError(f"schema success condition variant {condition_type} missing required fields")
        required_fields = {field for field in raw_required if isinstance(field, str)}
        if "id" not in required_fields or "type" not in required_fields:
            raise ValueError(f"schema success condition variant {condition_type} must require id and type")
        schema_required_fields[condition_type] = frozenset(required_fields - {"id", "type"})

    if schema_required_fields != SCHEMA_REQUIRED_CONDITION_FIELDS:
        raise ValueError("schema success condition variants drifted from contract model")
