from __future__ import annotations

import pytest

from scripts.preflight import main as preflight_main
from src.contract_model import load_contract, validate_contract
from tests.helpers import build_sample_workspace, write_contract, write_file


def test_validate_contract_rejects_unknown_condition_type() -> None:
    contract = {
        "version": 2,
        "task_id": "invalid-001",
        "goal": "Reject malformed contract",
        "inputs": {
            "repo_root": ".",
            "allowed_paths": ["src/**"],
        },
        "success_conditions": [
            {
                "id": "broken",
                "type": "unsupported",
                "command": "python -m pytest -q",
            },
            {
                "id": "smoke-check",
                "type": "verifier_stdout_contains",
                "command": "python scripts/smoke.py",
                "contains": "OK",
            },
        ],
        "evidence": {
            "output_dir": ".artifacts",
            "save_stdout": True,
            "save_stderr": True,
            "save_exit_codes": True,
            "hash_algorithm": "sha256",
            "freshness_path": ".truth/latest_run_id.txt",
        },
        "policy": {
            "fail_closed": True,
            "executor_cannot_claim_success": True,
            "verifier_is_final_authority": True,
            "require_black_box_verification": True,
            "reserved_outcome_words": [
                "PASS",
                "FAIL",
                "passed",
                "verified",
                "complete",
                "ready",
                "successful",
            ],
        },
    }

    with pytest.raises(ValueError, match="unsupported success condition type"):
        _ = validate_contract(contract)


def test_load_contract_rejects_duplicate_yaml_keys(tmp_path) -> None:
    build_sample_workspace(tmp_path)
    contract_path = tmp_path / "workspace.success.yaml"
    write_file(
        contract_path,
        "\n".join(
            [
                "version: 2",
                'task_id: "test-001"',
                'task_id: "test-002"',
                'goal: "Duplicate keys are invalid"',
                "inputs:",
                '  repo_root: "."',
                "  allowed_paths:",
                '    - "src/**"',
                "success_conditions:",
                '  - id: "smoke-check"',
                '    type: "verifier_stdout_contains"',
                '    command: "python scripts/smoke.py"',
                '    contains: "OK"',
                "evidence:",
                '  output_dir: ".artifacts"',
                "  save_stdout: true",
                "  save_stderr: true",
                "  save_exit_codes: true",
                '  hash_algorithm: "sha256"',
                '  freshness_path: ".truth/latest_run_id.txt"',
                "policy:",
                "  fail_closed: true",
                "  executor_cannot_claim_success: true",
                "  verifier_is_final_authority: true",
                "  require_black_box_verification: true",
                "  reserved_outcome_words:",
                '    - "PASS"',
            ]
        )
        + "\n",
    )

    with pytest.raises(ValueError, match="duplicate mapping key"):
        _ = load_contract(contract_path)


def test_preflight_rejects_unknown_schema_keys(tmp_path, capsys, monkeypatch) -> None:
    build_sample_workspace(tmp_path)
    contract_path = write_contract(
        tmp_path,
        success_conditions=[
            {
                "id": "smoke-check",
                "type": "verifier_stdout_contains",
                "command": "python scripts/smoke.py",
                "contains": "OK",
            }
        ],
    )
    original = contract_path.read_text(encoding="utf-8")
    write_file(
        contract_path,
        original.replace("policy:\n", "policy:\n  extra: true\n", 1),
    )

    monkeypatch.chdir(tmp_path)
    exit_code = preflight_main(["preflight.py", str(contract_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out.strip() == "INVALID"


def test_preflight_accepts_valid_contract_without_lock_file(tmp_path, capsys, monkeypatch) -> None:
    build_sample_workspace(tmp_path)
    write_file(tmp_path / "scripts/black_box.py", "print('OK')\n")
    contract_path = write_contract(
        tmp_path,
        success_conditions=[
            {
                "id": "smoke-check",
                "type": "verifier_stdout_contains",
                "command": "python scripts/black_box.py",
                "contains": "OK",
            }
        ],
    )

    monkeypatch.chdir(tmp_path)
    exit_code = preflight_main(["preflight.py", str(contract_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "VALID"
