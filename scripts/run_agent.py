from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.contract_model import SuccessCondition, load_contract  # noqa: E402
from src.evidence import contains_reserved_word, ensure_within, sha256_bytes, sha256_file  # noqa: E402


class ManifestEntry(TypedDict):
    id: str
    type: str
    command: str
    timestamp: str
    contract_sha256: str
    stdout_path: str
    stderr_path: str
    exit_code_path: str
    meta_path: str
    artifact_hashes: dict[str, str]


class EvidenceIndex(TypedDict):
    contract_sha256: str
    hash_algorithm: str
    artifacts: dict[str, str]


def ensure_output_dir(repo_root: Path, output_dir_text: str) -> Path:
    output_dir = repo_root / output_dir_text
    resolved_output = ensure_within(repo_root, output_dir, name="evidence.output_dir")
    resolved_output.mkdir(parents=True, exist_ok=True)
    return resolved_output


def write_text(path: Path, content: str) -> None:
    _ = path.write_text(content, encoding="utf-8")


def ensure_reserved_words_absent(text: str, reserved_words: list[str], *, name: str) -> None:
    matched = contains_reserved_word(text, reserved_words)
    if matched is not None:
        raise ValueError(f"{name} contains reserved outcome word: {matched}")


def write_json(
    path: Path,
    payload: object,
    *,
    reserved_words: list[str],
    enforce_reserved_words: bool = True,
) -> str:
    rendered = json.dumps(payload, indent=2) + "\n"
    if enforce_reserved_words:
        ensure_reserved_words_absent(rendered, reserved_words, name=path.name)
    write_text(path, rendered)
    return sha256_file(path)


def emit_executor_line(message: str, reserved_words: list[str]) -> None:
    ensure_reserved_words_absent(message, reserved_words, name="executor output")
    print(message)


def execute_condition(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        shell=True,
        check=False,
    )


def iter_executor_conditions(conditions: list[SuccessCondition]) -> list[SuccessCondition]:
    return [condition for condition in conditions if condition.is_executor_run()]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("execution requires a contract path")
        return 2

    repo_root = Path.cwd().resolve()

    try:
        contract_path = Path(argv[1]).resolve()
        contract = load_contract(contract_path)
        output_dir = ensure_output_dir(repo_root, contract.evidence.output_dir)
        contract_sha256 = sha256_bytes(contract_path.read_bytes())
        reserved_words = contract.policy.reserved_outcome_words
    except Exception:  # noqa: BLE001
        print("execution error")
        return 2

    manifest: dict[str, ManifestEntry] = {}
    artifact_index: dict[str, str] = {}

    try:
        for condition in iter_executor_conditions(contract.success_conditions):
            condition_id = condition.id
            started_at = datetime.now(timezone.utc).isoformat()
            result = execute_condition(condition.require_command())

            stdout_path = output_dir / f"{condition_id}.stdout.txt"
            stderr_path = output_dir / f"{condition_id}.stderr.txt"
            exit_code_path = output_dir / f"{condition_id}.exitcode.txt"
            meta_path = output_dir / f"{condition_id}.meta.json"

            write_text(stdout_path, result.stdout)
            write_text(stderr_path, result.stderr)
            write_text(exit_code_path, f"{result.returncode}\n")

            meta_payload = {
                "id": condition_id,
                "type": condition.type,
                "command": condition.require_command(),
                "timestamp": started_at,
                "contract_sha256": contract_sha256,
            }
            meta_hash = write_json(meta_path, meta_payload, reserved_words=reserved_words)

            stdout_hash = sha256_file(stdout_path)
            stderr_hash = sha256_file(stderr_path)
            exit_code_hash = sha256_file(exit_code_path)

            artifact_hashes = {
                stdout_path.name: stdout_hash,
                stderr_path.name: stderr_hash,
                exit_code_path.name: exit_code_hash,
                meta_path.name: meta_hash,
            }
            artifact_index.update(artifact_hashes)

            manifest[condition_id] = ManifestEntry(
                id=condition_id,
                type=condition.type,
                command=condition.require_command(),
                timestamp=started_at,
                contract_sha256=contract_sha256,
                stdout_path=stdout_path.name,
                stderr_path=stderr_path.name,
                exit_code_path=exit_code_path.name,
                meta_path=meta_path.name,
                artifact_hashes=artifact_hashes,
            )
            emit_executor_line(f"executed {condition_id}", reserved_words)

        manifest_path = output_dir / "execution_manifest.json"
        manifest_hash = write_json(manifest_path, manifest, reserved_words=reserved_words)
        artifact_index[manifest_path.name] = manifest_hash

        index_path = output_dir / "evidence_index.json"
        evidence_index: EvidenceIndex = {
            "contract_sha256": contract_sha256,
            "hash_algorithm": contract.evidence.hash_algorithm,
            "artifacts": artifact_index,
        }
        _ = write_json(index_path, evidence_index, reserved_words=reserved_words)
    except Exception:  # noqa: BLE001
        print("execution error")
        return 2

    emit_executor_line(f"collected evidence in {output_dir}", reserved_words)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
