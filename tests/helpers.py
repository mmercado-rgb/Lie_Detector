from __future__ import annotations

import json
from pathlib import Path


DEFAULT_RESERVED_WORDS = [
    "PASS",
    "FAIL",
    "passed",
    "verified",
    "complete",
    "ready",
    "successful",
]


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(content, encoding="utf-8")


def write_contract(
    root: Path,
    *,
    success_conditions: list[dict[str, str]],
    output_dir: str = ".artifacts",
    freshness_path: str = ".truth/latest_run_id.txt",
    require_black_box_verification: bool = True,
    reserved_outcome_words: list[str] | None = None,
) -> Path:
    reserved_words = reserved_outcome_words or DEFAULT_RESERVED_WORDS
    contract = {
        "version": 2,
        "task_id": "test-001",
        "goal": "Exercise contract flow",
        "inputs": {
            "repo_root": ".",
        },
        "success_conditions": success_conditions,
        "evidence": {
            "output_dir": output_dir,
            "save_stdout": True,
            "save_stderr": True,
            "save_exit_codes": True,
            "hash_algorithm": "sha256",
            "freshness_path": freshness_path,
        },
        "policy": {
            "fail_closed": True,
            "executor_cannot_claim_success": True,
            "verifier_is_final_authority": True,
            "require_black_box_verification": require_black_box_verification,
            "reserved_outcome_words": reserved_words,
        },
    }

    contract_path = root / "workspace.success.json"
    write_file(contract_path, json.dumps(contract, indent=2) + "\n")
    return contract_path


def build_sample_workspace(root: Path) -> None:
    write_file(root / "src/app.py", "def marker() -> str:\n    return 'ok'\n")
