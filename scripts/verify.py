from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, TypedDict, cast

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.contract_model import SuccessCondition  # noqa: E402
from src.continuity import load_latest_verified_run_id, parse_run_id, write_latest_verified_run_id  # noqa: E402
from src.evidence import ensure_relative_artifact_path, ensure_within, sha256_bytes, sha256_file  # noqa: E402
from src.integrity import (  # noqa: E402
    load_contract_with_integrity_gate,
    load_integrity_lock,
    validate_lock_binding,
)


class ManifestEntry(TypedDict):
    id: str
    type: str
    command: str
    timestamp: str
    run_id: str
    contract_sha256: str
    stdout_path: str
    stderr_path: str
    exit_code_path: str
    meta_path: str
    artifact_hashes: dict[str, str]


class ExecutionManifest(TypedDict):
    run_id: str
    previous_run_id: str | None
    entries: dict[str, ManifestEntry]


class EvidenceIndex(TypedDict):
    contract_sha256: str
    run_id: str
    previous_run_id: str | None
    hash_algorithm: str
    artifacts: dict[str, str]


class ConditionResult(TypedDict):
    id: str
    type: str
    measurable: bool
    ok: bool
    details: str


class VerifyResult(TypedDict):
    status: Literal["PASS", "FAIL"]
    conditions: list[ConditionResult]
    reasons: list[str]
    contract_sha256: str
    verification_timestamp: str


VERIFY_RESULT_FILENAME = "verify_result.json"
VERIFY_OUTPUT_DIRNAME = "verify"
EVIDENCE_INDEX_FILENAME = "evidence_index.json"


def write_result(output_dir: Path, payload: VerifyResult) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "verify_result.json"
    _ = result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def require_object_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain a mapping")
    raw_mapping = cast(dict[object, object], value)
    keys: list[object] = list(raw_mapping.keys())
    if not all(isinstance(key, str) for key in keys):
        raise ValueError(f"{name} must use string keys")
    return cast(Mapping[str, object], raw_mapping)


def require_non_empty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def require_run_id(value: object, name: str) -> str:
    return parse_run_id(value, name)


def require_nullable_run_id(value: object, name: str) -> str | None:
    if value is None:
        return None
    return require_run_id(value, name)


def require_str_dict(value: object, name: str) -> dict[str, str]:
    mapping = require_object_mapping(value, name)
    parsed: dict[str, str] = {}
    for key, raw_value in mapping.items():
        parsed[key] = require_non_empty_string(raw_value, f"{name}.{key}")
    return parsed


def load_json_object(path: Path, name: str) -> Mapping[str, object]:
    if not path.exists():
        raise ValueError(f"missing {name}")
    raw = cast(object, json.loads(path.read_text(encoding="utf-8")))
    return require_object_mapping(raw, name)


def load_manifest(output_dir: Path) -> tuple[ExecutionManifest, Path]:
    manifest_path = output_dir / "execution_manifest.json"
    data = load_json_object(manifest_path, "execution_manifest.json")
    required_fields = frozenset({"run_id", "previous_run_id", "entries"})
    unknown = set(data) - required_fields
    missing = required_fields - set(data)
    if "run_id" in missing:
        raise ValueError("current manifest is missing run_id")
    if "previous_run_id" in missing:
        raise ValueError("current manifest is missing previous_run_id")
    if missing:
        raise ValueError(f"execution_manifest.json missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"execution_manifest.json has unknown fields: {', '.join(sorted(unknown))}")

    entries_data = require_object_mapping(data.get("entries"), "execution_manifest.json.entries")
    entries: dict[str, ManifestEntry] = {}
    for key, value in entries_data.items():
        entry_data = require_object_mapping(value, f"execution_manifest entry {key}")
        required_fields = frozenset(
            {
                "id",
                "type",
                "command",
                "timestamp",
                "run_id",
                "contract_sha256",
                "stdout_path",
                "stderr_path",
                "exit_code_path",
                "meta_path",
                "artifact_hashes",
            }
        )
        unknown = set(entry_data) - required_fields
        missing = required_fields - set(entry_data)
        if missing:
            raise ValueError(f"execution_manifest entry {key} missing fields: {', '.join(sorted(missing))}")
        if unknown:
            raise ValueError(f"execution_manifest entry {key} has unknown fields: {', '.join(sorted(unknown))}")

        artifact_hashes = require_str_dict(
            entry_data.get("artifact_hashes"),
            f"execution_manifest entry {key}.artifact_hashes",
        )
        entries[key] = ManifestEntry(
            id=require_non_empty_string(entry_data.get("id"), f"execution_manifest entry {key}.id"),
            type=require_non_empty_string(entry_data.get("type"), f"execution_manifest entry {key}.type"),
            command=require_non_empty_string(entry_data.get("command"), f"execution_manifest entry {key}.command"),
            timestamp=require_non_empty_string(
                entry_data.get("timestamp"),
                f"execution_manifest entry {key}.timestamp",
            ),
            run_id=require_run_id(entry_data.get("run_id"), f"execution_manifest entry {key}.run_id"),
            contract_sha256=require_non_empty_string(
                entry_data.get("contract_sha256"),
                f"execution_manifest entry {key}.contract_sha256",
            ),
            stdout_path=require_non_empty_string(
                entry_data.get("stdout_path"),
                f"execution_manifest entry {key}.stdout_path",
            ),
            stderr_path=require_non_empty_string(
                entry_data.get("stderr_path"),
                f"execution_manifest entry {key}.stderr_path",
            ),
            exit_code_path=require_non_empty_string(
                entry_data.get("exit_code_path"),
                f"execution_manifest entry {key}.exit_code_path",
            ),
            meta_path=require_non_empty_string(
                entry_data.get("meta_path"),
                f"execution_manifest entry {key}.meta_path",
            ),
            artifact_hashes=artifact_hashes,
        )
    return (
        ExecutionManifest(
            run_id=require_run_id(data.get("run_id"), "execution_manifest.json.run_id"),
            previous_run_id=require_nullable_run_id(
                data.get("previous_run_id"),
                "execution_manifest.json.previous_run_id",
            ),
            entries=entries,
        ),
        manifest_path,
    )


def load_evidence_index(output_dir: Path) -> EvidenceIndex:
    path = output_dir / "evidence_index.json"
    data = load_json_object(path, "evidence_index.json")
    required_fields = frozenset({"contract_sha256", "run_id", "previous_run_id", "hash_algorithm", "artifacts"})
    unknown = set(data) - required_fields
    missing = required_fields - set(data)
    if missing:
        raise ValueError(f"evidence_index.json missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"evidence_index.json has unknown fields: {', '.join(sorted(unknown))}")
    return EvidenceIndex(
        contract_sha256=require_non_empty_string(data.get("contract_sha256"), "evidence_index.json.contract_sha256"),
        run_id=require_run_id(data.get("run_id"), "evidence_index.json.run_id"),
        previous_run_id=require_nullable_run_id(
            data.get("previous_run_id"),
            "evidence_index.json.previous_run_id",
        ),
        hash_algorithm=require_non_empty_string(data.get("hash_algorithm"), "evidence_index.json.hash_algorithm"),
        artifacts=require_str_dict(data.get("artifacts"), "evidence_index.json.artifacts"),
    )


def read_exit_code(path: Path, condition_id: str) -> int:
    text = path.read_text(encoding="utf-8").strip()
    if not text or any(ch not in "-0123456789" for ch in text):
        raise ValueError(f"ambiguous exit code evidence for {condition_id}")
    return int(text)


def execute_command(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        shell=True,
        check=False,
    )


def verify_meta_file(meta_path: Path, entry: ManifestEntry, condition_id: str) -> None:
    data = load_json_object(meta_path, f"{condition_id}.meta.json")
    expected = {
        "id": entry["id"],
        "type": entry["type"],
        "command": entry["command"],
        "timestamp": entry["timestamp"],
        "run_id": entry["run_id"],
        "contract_sha256": entry["contract_sha256"],
    }
    if set(data) != set(expected):
        raise ValueError(f"metadata fields do not match expected shape for {condition_id}")
    for field_name, field_value in expected.items():
        actual = data.get(field_name)
        if actual != field_value:
            raise ValueError(f"metadata mismatch for {condition_id}: {field_name}")


def verify_executor_entry(
    condition: SuccessCondition,
    entry: ManifestEntry,
    output_dir: Path,
    evidence_index: EvidenceIndex,
    contract_sha256: str,
) -> tuple[Path, Path]:
    if entry["id"] != condition.id:
        raise ValueError(f"manifest id mismatch for {condition.id}")
    if entry["type"] != condition.type:
        raise ValueError(f"manifest type mismatch for {condition.id}")
    if entry["command"] != condition.require_command():
        raise ValueError(f"manifest command mismatch for {condition.id}")
    if entry["run_id"] != evidence_index["run_id"]:
        raise ValueError(f"manifest run_id mismatch for {condition.id}")
    if entry["contract_sha256"] != contract_sha256:
        raise ValueError(f"manifest contract hash mismatch for {condition.id}")

    artifact_names = {
        entry["stdout_path"],
        entry["stderr_path"],
        entry["exit_code_path"],
        entry["meta_path"],
    }
    if set(entry["artifact_hashes"]) != artifact_names:
        raise ValueError(f"artifact hash manifest mismatch for {condition.id}")

    for artifact_name in artifact_names:
        artifact_path = ensure_relative_artifact_path(
            output_dir,
            artifact_name,
            name=f"{condition.id}.{artifact_name}",
        )
        if not artifact_path.exists():
            raise ValueError(f"missing evidence file for {condition.id}: {artifact_name}")
        actual_hash = sha256_file(artifact_path)
        indexed_hash = evidence_index["artifacts"].get(artifact_name)
        manifest_hash = entry["artifact_hashes"].get(artifact_name)
        if indexed_hash is None:
            raise ValueError(f"missing evidence index entry for {artifact_name}")
        if indexed_hash != manifest_hash:
            raise ValueError(f"hash disagreement for {artifact_name}")
        if indexed_hash != actual_hash:
            raise ValueError(f"tampered evidence detected for {artifact_name}")

    meta_path = ensure_relative_artifact_path(output_dir, entry["meta_path"], name=f"{condition.id}.meta_path")
    verify_meta_file(meta_path, entry, condition.id)
    stdout_path = ensure_relative_artifact_path(
        output_dir,
        entry["stdout_path"],
        name=f"{condition.id}.stdout_path",
    )
    exit_code_path = ensure_relative_artifact_path(
        output_dir,
        entry["exit_code_path"],
        name=f"{condition.id}.exit_code_path",
    )
    return stdout_path, exit_code_path


def evaluate_executor_condition(
    condition: SuccessCondition,
    stdout_path: Path,
    exit_code_path: Path,
) -> ConditionResult:
    record: ConditionResult = {
        "id": condition.id,
        "type": condition.type,
        "measurable": True,
        "ok": False,
        "details": "",
    }
    exit_code = read_exit_code(exit_code_path, condition.id)
    if condition.type == "command_exit_zero":
        record["ok"] = exit_code == 0
        record["details"] = f"exit_code={exit_code}"
        return record

    stdout_text = stdout_path.read_text(encoding="utf-8")
    required_text = condition.require_contains()
    record["ok"] = required_text in stdout_text
    record["details"] = f"contains={required_text!r}"
    return record


def evaluate_file_exists(condition: SuccessCondition, repo_root: Path) -> ConditionResult:
    target = ensure_within(repo_root, repo_root / condition.require_path(), name=f"{condition.id}.path")
    return ConditionResult(
        id=condition.id,
        type=condition.type,
        measurable=True,
        ok=target.exists(),
        details=f"path={target.as_posix()}",
    )


def evaluate_verifier_condition(condition: SuccessCondition, verify_dir: Path) -> ConditionResult:
    result = execute_command(condition.require_command())
    stdout_path = verify_dir / f"{condition.id}.stdout.txt"
    stderr_path = verify_dir / f"{condition.id}.stderr.txt"
    exit_code_path = verify_dir / f"{condition.id}.exitcode.txt"
    _ = stdout_path.write_text(result.stdout, encoding="utf-8")
    _ = stderr_path.write_text(result.stderr, encoding="utf-8")
    _ = exit_code_path.write_text(f"{result.returncode}\n", encoding="utf-8")

    record: ConditionResult = {
        "id": condition.id,
        "type": condition.type,
        "measurable": True,
        "ok": False,
        "details": "",
    }
    if condition.type == "verifier_command_exit_zero":
        record["ok"] = result.returncode == 0
        record["details"] = f"exit_code={result.returncode}"
        return record

    required_text = condition.require_contains()
    record["ok"] = required_text in result.stdout
    record["details"] = f"contains={required_text!r}"
    return record


def validate_manifest_and_index(
    contract_conditions: list[SuccessCondition],
    execution_manifest: ExecutionManifest,
    manifest_path: Path,
    evidence_index: EvidenceIndex,
    contract_sha256: str,
    expected_previous_run_id: str | None,
) -> None:
    manifest = execution_manifest["entries"]
    current_run_id = execution_manifest["run_id"]
    previous_run_id = execution_manifest["previous_run_id"]

    if evidence_index["hash_algorithm"] != "sha256":
        raise ValueError("unsupported evidence hash algorithm")
    if evidence_index["contract_sha256"] != contract_sha256:
        raise ValueError("evidence index contract hash mismatch")
    if evidence_index["run_id"] != current_run_id:
        raise ValueError("evidence run_id does not match current manifest")
    if evidence_index["previous_run_id"] != previous_run_id:
        raise ValueError("evidence previous_run_id does not match current manifest")
    if expected_previous_run_id is None and previous_run_id is not None:
        raise ValueError("a prior run is required but missing")
    if expected_previous_run_id is not None and previous_run_id != expected_previous_run_id:
        raise ValueError("previous_run_id does not match the expected prior run")

    executor_conditions = {condition.id: condition for condition in contract_conditions if condition.is_executor_run()}
    if set(manifest) != set(executor_conditions):
        missing = set(executor_conditions) - set(manifest)
        extra = set(manifest) - set(executor_conditions)
        if missing:
            raise ValueError(f"missing executor evidence entries: {', '.join(sorted(missing))}")
        raise ValueError(f"unexpected manifest entries: {', '.join(sorted(extra))}")

    referenced_artifacts: set[str] = {manifest_path.name}
    for condition_id, entry in manifest.items():
        if condition_id not in executor_conditions:
            raise ValueError(f"manifest contains undeclared condition: {condition_id}")
        entry_artifacts = {
            entry["stdout_path"],
            entry["stderr_path"],
            entry["exit_code_path"],
            entry["meta_path"],
        }
        overlap = referenced_artifacts & entry_artifacts
        if overlap:
            raise ValueError(f"duplicate artifact reference: {sorted(overlap)[0]}")
        referenced_artifacts.update(entry_artifacts)
        if entry["run_id"] != current_run_id:
            raise ValueError(f"manifest run_id mismatch for {condition_id}")
        if entry["contract_sha256"] != contract_sha256:
            raise ValueError(f"manifest contract hash mismatch for {condition_id}")

    indexed_artifacts = set(evidence_index["artifacts"])
    if indexed_artifacts != referenced_artifacts:
        missing = referenced_artifacts - indexed_artifacts
        extra = indexed_artifacts - referenced_artifacts
        if missing:
            raise ValueError(f"missing indexed artifacts: {', '.join(sorted(missing))}")
        raise ValueError(f"orphaned indexed artifacts: {', '.join(sorted(extra))}")

    manifest_hash = sha256_file(manifest_path)
    if evidence_index["artifacts"].get(manifest_path.name) != manifest_hash:
        raise ValueError("execution manifest hash mismatch")


def is_verifier_owned_artifact(path_text: str) -> bool:
    if path_text == VERIFY_RESULT_FILENAME:
        return True
    return path_text.startswith(f"{VERIFY_OUTPUT_DIRNAME}/")


def collect_artifact_inventory(output_dir: Path) -> set[str]:
    files: set[str] = set()
    for path in sorted(output_dir.rglob("*")):
        if path.is_file():
            files.add(path.relative_to(output_dir).as_posix())
    return files


def validate_artifact_inventory(output_dir: Path, evidence_index: EvidenceIndex) -> None:
    expected = set(evidence_index["artifacts"])
    expected.add(EVIDENCE_INDEX_FILENAME)
    actual = collect_artifact_inventory(output_dir)
    extras = sorted(path for path in (actual - expected) if not is_verifier_owned_artifact(path))
    if extras:
        raise ValueError(f"unexpected artifact files on disk: {', '.join(extras)}")


def verify_workspace(repo_root: Path, contract_path: Path) -> int:
    output_dir = repo_root / ".artifacts"
    result_payload: VerifyResult = {
        "status": "FAIL",
        "conditions": [],
        "reasons": [],
        "contract_sha256": "",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        contract = load_contract_with_integrity_gate(contract_path)
        lock_path = repo_root / ".truth" / "lock.json"
        if lock_path.exists():
            lock = load_integrity_lock(lock_path)
            validate_lock_binding(repo_root, contract, lock)
        output_dir = ensure_within(repo_root, repo_root / contract.evidence.output_dir, name="evidence.output_dir")
        output_dir.mkdir(parents=True, exist_ok=True)
        contract_sha256 = sha256_bytes(contract_path.read_bytes())
        result_payload["contract_sha256"] = contract_sha256

        execution_manifest, manifest_path = load_manifest(output_dir)
        evidence_index = load_evidence_index(output_dir)
        expected_previous_run_id = load_latest_verified_run_id(repo_root, contract.evidence.freshness_path)
        validate_manifest_and_index(
            contract.success_conditions,
            execution_manifest,
            manifest_path,
            evidence_index,
            contract_sha256,
            expected_previous_run_id,
        )
        validate_artifact_inventory(output_dir, evidence_index)

        verify_dir = output_dir / VERIFY_OUTPUT_DIRNAME
        verify_dir.mkdir(parents=True, exist_ok=True)

        manifest = execution_manifest["entries"]
        results: list[ConditionResult] = []
        for condition in contract.success_conditions:
            if condition.type == "file_exists":
                results.append(evaluate_file_exists(condition, repo_root))
                continue
            if condition.is_executor_run():
                entry = manifest.get(condition.id)
                if entry is None:
                    raise ValueError(f"missing evidence manifest entry for {condition.id}")
                stdout_path, exit_code_path = verify_executor_entry(
                    condition,
                    entry,
                    output_dir,
                    evidence_index,
                    contract_sha256,
                )
                results.append(evaluate_executor_condition(condition, stdout_path, exit_code_path))
                continue
            if condition.is_verifier_run():
                results.append(evaluate_verifier_condition(condition, verify_dir))
                continue
            raise ValueError(f"unsupported condition type at verification time: {condition.type}")

        result_payload["conditions"] = results
        result_payload["status"] = "PASS" if all(item["ok"] for item in results) else "FAIL"
        if result_payload["status"] == "PASS":
            write_latest_verified_run_id(
                repo_root,
                contract.evidence.freshness_path,
                execution_manifest["run_id"],
            )
    except Exception as exc:  # noqa: BLE001
        result_payload["reasons"] = [str(exc)]
        write_result(output_dir, result_payload)
        print("FAIL")
        return 1

    write_result(output_dir, result_payload)
    print(result_payload["status"])
    return 0 if result_payload["status"] == "PASS" else 1


def main(argv: list[str]) -> int:
    output_dir = REPO_ROOT / ".artifacts"
    result_payload: VerifyResult = {
        "status": "FAIL",
        "conditions": [],
        "reasons": [],
        "contract_sha256": "",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if len(argv) != 2:
        result_payload["reasons"] = ["entry path requires a contract path argument"]
        write_result(output_dir, result_payload)
        print("FAIL")
        return 1

    contract_path = Path(argv[1]).resolve()
    repo_root = contract_path.parent
    return verify_workspace(repo_root, contract_path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
