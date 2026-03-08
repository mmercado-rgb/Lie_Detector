from __future__ import annotations

import hashlib
import json

from scripts.run_agent import main as run_agent_main
from tests.helpers import build_sample_workspace, write_contract, write_file


def test_run_agent_writes_contract_hashes_and_evidence_index(tmp_path, capsys, monkeypatch) -> None:
    build_sample_workspace(tmp_path)
    write_file(tmp_path / "scripts/black_box.py", "print('BETA')\n")
    contract_path = write_contract(
        tmp_path,
        success_conditions=[
            {
                "id": "exec-check",
                "type": "command_stdout_contains",
                "command": 'python -c "print(\'ALPHA\')"',
                "contains": "ALPHA",
            },
            {
                "id": "required-file",
                "type": "file_exists",
                "path": "src/app.py",
            },
            {
                "id": "black-box",
                "type": "verifier_stdout_contains",
                "command": "python scripts/black_box.py",
                "contains": "BETA",
            },
        ],
    )

    monkeypatch.chdir(tmp_path)
    exit_code = run_agent_main(["run_agent.py", str(contract_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.splitlines()[0] == "executed exec-check"
    assert captured.out.splitlines()[-1] == f"collected evidence in {tmp_path / '.artifacts'}"
    assert "PASS" not in captured.out
    assert "FAIL" not in captured.out

    output_dir = tmp_path / ".artifacts"
    manifest = json.loads((output_dir / "execution_manifest.json").read_text(encoding="utf-8"))
    evidence_index = json.loads((output_dir / "evidence_index.json").read_text(encoding="utf-8"))
    contract_sha256 = hashlib.sha256(contract_path.read_bytes()).hexdigest()

    assert set(manifest) == {"exec-check"}
    entry = manifest["exec-check"]
    assert entry["contract_sha256"] == contract_sha256
    assert evidence_index["contract_sha256"] == contract_sha256
    assert evidence_index["hash_algorithm"] == "sha256"
    assert "execution_manifest.json" in evidence_index["artifacts"]

    for artifact_name, artifact_hash in entry["artifact_hashes"].items():
        artifact_path = output_dir / artifact_name
        assert artifact_path.exists()
        assert hashlib.sha256(artifact_path.read_bytes()).hexdigest() == artifact_hash
        assert evidence_index["artifacts"][artifact_name] == artifact_hash

    assert not (output_dir / "verify_result.json").exists()
    assert not (output_dir / "black-box.stdout.txt").exists()


def test_run_agent_rejects_reserved_outcome_words_in_metadata(tmp_path, capsys, monkeypatch) -> None:
    build_sample_workspace(tmp_path)
    write_file(tmp_path / "scripts/black_box.py", "print('SAFE')\n")
    contract_path = write_contract(
        tmp_path,
        success_conditions=[
            {
                "id": "exec-check",
                "type": "command_exit_zero",
                "command": "echo PASS",
            },
            {
                "id": "black-box",
                "type": "verifier_stdout_contains",
                "command": "python scripts/black_box.py",
                "contains": "SAFE",
            },
        ],
    )

    monkeypatch.chdir(tmp_path)
    exit_code = run_agent_main(["run_agent.py", str(contract_path)])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out.strip() == "execution error"
