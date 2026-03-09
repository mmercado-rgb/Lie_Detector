from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.contract_model import load_contract
from src.integrity import load_contract_with_integrity_gate
from tests.helpers import build_sample_workspace, write_contract


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ENTRYPOINTS = (
    ROOT / "scripts" / "preflight.py",
    ROOT / "scripts" / "run_agent.py",
    ROOT / "scripts" / "verify.py",
)
RUNTIME_FILES_ENFORCED = (
    ROOT / "scripts" / "preflight.py",
    ROOT / "scripts" / "run_agent.py",
    ROOT / "scripts" / "verify.py",
    ROOT / "src" / "evidence.py",
    ROOT / "src" / "app.py",
)
FORBIDDEN_PARSE_PATTERNS = (
    re.compile(r"\bload_contract\s*\("),
    re.compile(r"\bparse_contract_json\s*\("),
)


def test_runtime_entrypoints_always_load_contract_via_schema_gate() -> None:
    for path in RUNTIME_ENTRYPOINTS:
        text = path.read_text(encoding="utf-8")
        assert "load_contract_with_integrity_gate(" in text, f"{path} must call schema gate loader"


def test_runtime_files_do_not_parse_contract_outside_schema_gate() -> None:
    for path in RUNTIME_FILES_ENFORCED:
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PARSE_PATTERNS:
            assert pattern.search(text) is None, f"{path} contains forbidden contract parse pattern: {pattern.pattern}"


def test_direct_load_contract_api_is_forbidden(tmp_path: Path) -> None:
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

    with pytest.raises(ValueError, match="direct contract loading is forbidden"):
        _ = load_contract(contract_path)


def test_repo_root_workspace_contract_exists_and_passes_schema_gate() -> None:
    contract_path = ROOT / "workspace.success.json"
    assert contract_path.exists(), "repo root workspace.success.json must exist"
    _ = load_contract_with_integrity_gate(contract_path)
