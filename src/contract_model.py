from __future__ import annotations

import ast
import re
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
REQUIRED_TOP_LEVEL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "version",
        "task_id",
        "goal",
        "inputs",
        "success_conditions",
        "evidence",
        "policy",
    }
)
INPUT_KEYS: Final[frozenset[str]] = frozenset({"repo_root", "allowed_paths"})
EVIDENCE_KEYS: Final[frozenset[str]] = frozenset(
    {"output_dir", "save_stdout", "save_stderr", "save_exit_codes", "hash_algorithm"}
)
POLICY_KEYS: Final[frozenset[str]] = frozenset(
    {
        "fail_closed",
        "executor_cannot_claim_success",
        "verifier_is_final_authority",
        "require_black_box_verification",
        "reserved_outcome_words",
    }
)
BASE_CONDITION_KEYS: Final[frozenset[str]] = frozenset({"id", "type"})
FILE_EXISTS_KEYS: Final[frozenset[str]] = frozenset((*BASE_CONDITION_KEYS, "path"))
COMMAND_EXIT_ZERO_KEYS: Final[frozenset[str]] = frozenset((*BASE_CONDITION_KEYS, "command"))
STDOUT_CONTAINS_KEYS: Final[frozenset[str]] = frozenset(
    (*BASE_CONDITION_KEYS, "command", "contains")
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


class SimpleYamlError(ValueError):
    pass


class SimpleYamlParser:
    def __init__(self, text: str) -> None:
        self.lines: list[tuple[int, str]] = self._prepare_lines(text)
        self.index: int = 0

    def parse(self) -> object:
        if not self.lines:
            raise SimpleYamlError("yaml document is empty")
        value = self._parse_block(self.lines[0][0])
        if self.index != len(self.lines):
            raise SimpleYamlError("yaml document has trailing content")
        return value

    def _prepare_lines(self, text: str) -> list[tuple[int, str]]:
        prepared: list[tuple[int, str]] = []
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            prepared.append((indent, raw_line[indent:]))
        return prepared

    def _parse_block(self, indent: int) -> object:
        current_indent, content = self.lines[self.index]
        if current_indent != indent:
            raise SimpleYamlError("invalid indentation")
        if content.startswith("- "):
            return self._parse_list(indent)
        return self._parse_mapping(indent)

    def _parse_mapping(self, indent: int) -> dict[str, object]:
        mapping: dict[str, object] = {}
        while self.index < len(self.lines):
            current_indent, content = self.lines[self.index]
            if current_indent < indent:
                break
            if current_indent != indent:
                raise SimpleYamlError("unexpected indentation in mapping")
            if content.startswith("- "):
                raise SimpleYamlError("list item found where mapping entry was expected")
            key, value_text = self._split_key_value(content)
            if key in mapping:
                raise SimpleYamlError(f"duplicate mapping key: {key}")
            self.index += 1
            mapping[key] = self._parse_value_or_nested_block(indent, value_text)
        return mapping

    def _parse_list(self, indent: int) -> list[object]:
        items: list[object] = []
        while self.index < len(self.lines):
            current_indent, content = self.lines[self.index]
            if current_indent < indent:
                break
            if current_indent != indent or not content.startswith("- "):
                raise SimpleYamlError("unexpected content in list")
            self.index += 1
            item_text = content[2:].strip()
            if not item_text:
                if self.index >= len(self.lines) or self.lines[self.index][0] <= indent:
                    raise SimpleYamlError("list item requires a value")
                items.append(self._parse_block(indent + 2))
                continue
            if ":" in item_text:
                key, value_text = self._split_key_value(item_text)
                item_mapping: dict[str, object] = {}
                if key in item_mapping:
                    raise SimpleYamlError(f"duplicate mapping key: {key}")
                item_mapping[key] = self._parse_value_or_nested_block(indent, value_text)
                tail = self._parse_list_item_mapping_tail(indent)
                duplicate_keys = set(item_mapping) & set(tail)
                if duplicate_keys:
                    raise SimpleYamlError(
                        f"duplicate mapping key: {sorted(duplicate_keys)[0]}"
                    )
                item_mapping.update(tail)
                items.append(item_mapping)
                continue
            items.append(self._parse_scalar(item_text))
        return items

    def _parse_list_item_mapping_tail(self, indent: int) -> dict[str, object]:
        mapping: dict[str, object] = {}
        while self.index < len(self.lines):
            current_indent, content = self.lines[self.index]
            if current_indent <= indent:
                break
            if current_indent != indent + 2 or content.startswith("- "):
                raise SimpleYamlError("invalid list item mapping indentation")
            key, value_text = self._split_key_value(content)
            if key in mapping:
                raise SimpleYamlError(f"duplicate mapping key: {key}")
            self.index += 1
            mapping[key] = self._parse_value_or_nested_block(indent + 2, value_text)
        return mapping

    def _parse_value_or_nested_block(self, parent_indent: int, value_text: str) -> object:
        if value_text:
            return self._parse_scalar(value_text)
        if self.index >= len(self.lines) or self.lines[self.index][0] <= parent_indent:
            return None
        return self._parse_block(parent_indent + 2)

    def _split_key_value(self, content: str) -> tuple[str, str]:
        if ":" not in content:
            raise SimpleYamlError("mapping entry is missing ':'")
        key, value_text = content.split(":", 1)
        key_text = key.strip()
        if not key_text:
            raise SimpleYamlError("mapping key must be non-empty")
        return key_text, value_text.strip()

    def _parse_scalar(self, value_text: str) -> object:
        lowered = value_text.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered in {"null", "~"}:
            return None
        if (
            value_text.startswith(("'", '"'))
            and value_text.endswith(("'", '"'))
            and len(value_text) >= 2
        ):
            return cast(object, ast.literal_eval(value_text))
        if value_text.lstrip("-").isdigit():
            return int(value_text)
        return value_text


def load_contract(contract_path: Path) -> Contract:
    try:
        data = SimpleYamlParser(contract_path.read_text(encoding="utf-8")).parse()
    except FileNotFoundError as exc:
        raise ValueError(f"contract file not found: {contract_path}") from exc
    except SimpleYamlError as exc:
        raise ValueError(f"contract yaml parse error: {exc}") from exc
    return validate_contract(data)


def require_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    raw_mapping = cast(dict[object, object], value)
    keys: list[object] = list(raw_mapping.keys())
    if not all(isinstance(key, str) for key in keys):
        raise ValueError(f"{name} must use string keys")
    return cast(Mapping[str, object], raw_mapping)


def require_exact_keys(
    mapping: Mapping[str, object],
    name: str,
    expected_keys: frozenset[str],
) -> None:
    missing_keys = expected_keys - set(mapping)
    unknown_keys = set(mapping) - expected_keys
    if missing_keys:
        raise ValueError(f"{name} missing keys: {', '.join(sorted(missing_keys))}")
    if unknown_keys:
        raise ValueError(f"{name} has unknown keys: {', '.join(sorted(unknown_keys))}")


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


def require_string_list(value: object, name: str) -> list[str]:
    raw_list = require_non_empty_list(value, name)
    parsed = [require_non_empty_string(item, f"{name}[{index}]") for index, item in enumerate(raw_list)]
    if len(set(parsed)) != len(parsed):
        raise ValueError(f"{name} must not contain duplicates")
    return parsed


def parse_inputs(inputs_value: object) -> Inputs:
    inputs = require_mapping(inputs_value, "inputs")
    require_exact_keys(inputs, "inputs", INPUT_KEYS)
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
    require_exact_keys(evidence, "evidence", EVIDENCE_KEYS)
    hash_algorithm = require_non_empty_string(evidence.get("hash_algorithm"), "evidence.hash_algorithm")
    if hash_algorithm not in HASH_ALGORITHMS:
        raise ValueError(f"unsupported evidence.hash_algorithm: {hash_algorithm}")
    return Evidence(
        output_dir=require_repo_relative_path(evidence.get("output_dir"), "evidence.output_dir"),
        save_stdout=require_bool(evidence.get("save_stdout"), "evidence.save_stdout"),
        save_stderr=require_bool(evidence.get("save_stderr"), "evidence.save_stderr"),
        save_exit_codes=require_bool(evidence.get("save_exit_codes"), "evidence.save_exit_codes"),
        hash_algorithm=hash_algorithm,
    )


def parse_policy(policy_value: object) -> Policy:
    policy = require_mapping(policy_value, "policy")
    require_exact_keys(policy, "policy", POLICY_KEYS)
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
    if condition_type == "file_exists":
        require_exact_keys(condition, f"success_conditions[{index}]", FILE_EXISTS_KEYS)
    elif condition_type in {"command_stdout_contains", "verifier_stdout_contains"}:
        require_exact_keys(condition, f"success_conditions[{index}]", STDOUT_CONTAINS_KEYS)
    else:
        require_exact_keys(condition, f"success_conditions[{index}]", COMMAND_EXIT_ZERO_KEYS)

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
    require_exact_keys(contract, "contract", REQUIRED_TOP_LEVEL_KEYS)

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
