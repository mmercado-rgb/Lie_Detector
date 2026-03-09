from __future__ import annotations

import hashlib
import json

from scripts.preflight import main as preflight_main
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
    assert len(evidence_index["run_id"]) == 32
    assert evidence_index["hash_algorithm"] == "sha256"
    assert "execution_manifest.json" in evidence_index["artifacts"]
    assert (tmp_path / ".truth" / "latest_run_id.txt").read_text(encoding="utf-8").strip() == evidence_index["run_id"]

    for artifact_name, artifact_hash in entry["artifact_hashes"].items():
        artifact_path = output_dir / artifact_name
        assert artifact_path.exists()
        assert hashlib.sha256(artifact_path.read_bytes()).hexdigest() == artifact_hash
        assert evidence_index["artifacts"][artifact_name] == artifact_hash
    assert entry["run_id"] == evidence_index["run_id"]

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


def test_run_agent_refuses_invalid_contract_and_writes_no_artifacts(
    tmp_path, capsys, monkeypatch
) -> None:
    build_sample_workspace(tmp_path)
    write_file(tmp_path / "scripts/black_box.py", "print('SAFE')\n")
    contract_path = write_contract(
        tmp_path,
        success_conditions=[
            {
                "id": "exec-check",
                "type": "command_exit_zero",
                "command": 'python -c "from pathlib import Path; Path(\'unexpected.txt\').write_text(\'x\')"',
            },
            {
                "id": "black-box",
                "type": "verifier_stdout_contains",
                "command": "python scripts/black_box.py",
                "contains": "SAFE",
            },
        ],
    )
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    payload["policy"]["extra"] = True
    write_file(contract_path, json.dumps(payload, indent=2) + "\n")

    output_dir = tmp_path / ".artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)
    write_file(output_dir / ".gitkeep", "")

    monkeypatch.chdir(tmp_path)
    assert preflight_main(["preflight.py", str(contract_path)]) == 1
    _ = capsys.readouterr()

    before_files = {path.name for path in output_dir.iterdir() if path.is_file()}
    exit_code = run_agent_main(["run_agent.py", str(contract_path)])
    captured = capsys.readouterr()
    after_files = {path.name for path in output_dir.iterdir() if path.is_file()}

    assert exit_code != 0
    assert captured.out.strip() == "execution error"
    assert before_files == {".gitkeep"}
    assert after_files == before_files
    assert not (tmp_path / "unexpected.txt").exists()

def test_run_agent_blocks_outside_workspace_write_attempt(tmp_path, capsys, monkeypatch) -> None:
    build_sample_workspace(tmp_path)
    contract_path = write_contract(
        tmp_path,
        success_conditions=[
            {
                "id": "escape-attempt",
                "type": "command_exit_zero",
                "command": 'python -c "from pathlib import Path; Path(\'../escape.txt\').write_text(\'x\', encoding=\'utf-8\')"',
            }
        ],
    )

    monkeypatch.chdir(tmp_path)
    exit_code = run_agent_main(["run_agent.py", str(contract_path)])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert captured.out.strip() == "execution error"
    assert not (tmp_path.parent / "escape.txt").exists()
    assert not (tmp_path / ".artifacts" / "execution_manifest.json").exists()

def test_run_agent_blocks_absolute_outside_write_attempt(tmp_path, capsys, monkeypatch) -> None:
    build_sample_workspace(tmp_path)
    outside_path = tmp_path.parent / "tmp_escape.txt"
    contract_path = write_contract(
        tmp_path,
        success_conditions=[
            {
                "id": "absolute-escape-attempt",
                "type": "command_exit_zero",
                "command": f'python -c "from pathlib import Path; Path(r\'{outside_path}\').write_text(\'x\', encoding=\'utf-8\')"',
            }
        ],
    )

    monkeypatch.chdir(tmp_path)
    exit_code = run_agent_main(["run_agent.py", str(contract_path)])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert captured.out.strip() == "execution error"
    assert not outside_path.exists()

