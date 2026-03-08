from __future__ import annotations

import hashlib
import json

from scripts.run_agent import main as run_agent_main
from scripts.verify import main as verify_main
from tests.helpers import build_sample_workspace, write_contract, write_file


def prepare_workspace(tmp_path, monkeypatch):
    build_sample_workspace(tmp_path)
    write_file(
        tmp_path / "scripts/black_box.py",
        "\n".join(
            [
                "from pathlib import Path",
                "",
                "print(Path('probe.txt').read_text(encoding='utf-8').strip())",
            ]
        )
        + "\n",
    )
    write_file(tmp_path / "probe.txt", "FIRST\n")
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
                "contains": "SECOND",
            },
        ],
    )
    monkeypatch.chdir(tmp_path)
    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    return contract_path


def test_verify_fails_when_manifest_command_differs_from_contract(tmp_path, capsys, monkeypatch) -> None:
    contract_path = prepare_workspace(tmp_path, monkeypatch)
    output_dir = tmp_path / ".artifacts"
    _ = capsys.readouterr()

    manifest_path = output_dir / "execution_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["exec-check"]["command"] = 'python -c "print(\'BETA\')"'
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    evidence_index_path = output_dir / "evidence_index.json"
    evidence_index = json.loads(evidence_index_path.read_text(encoding="utf-8"))
    evidence_index["artifacts"]["execution_manifest.json"] = hashlib.sha256(
        manifest_path.read_bytes()
    ).hexdigest()
    evidence_index_path.write_text(json.dumps(evidence_index, indent=2) + "\n", encoding="utf-8")

    exit_code = verify_main(["verify.py", str(contract_path)])
    captured = capsys.readouterr()
    result_payload = json.loads((output_dir / "verify_result.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert captured.out.strip() == "FAIL"
    assert result_payload["status"] == "FAIL"
    assert result_payload["reasons"] == ["manifest command mismatch for exec-check"]


def test_verify_fails_on_tampered_evidence(tmp_path, capsys, monkeypatch) -> None:
    contract_path = prepare_workspace(tmp_path, monkeypatch)
    output_dir = tmp_path / ".artifacts"
    _ = capsys.readouterr()
    write_file(output_dir / "exec-check.stdout.txt", "MUTATED\n")

    exit_code = verify_main(["verify.py", str(contract_path)])
    captured = capsys.readouterr()
    result_payload = json.loads((output_dir / "verify_result.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert captured.out.strip() == "FAIL"
    assert result_payload["status"] == "FAIL"
    assert result_payload["reasons"] == ["tampered evidence detected for exec-check.stdout.txt"]


def test_verify_fails_on_missing_evidence(tmp_path, capsys, monkeypatch) -> None:
    contract_path = prepare_workspace(tmp_path, monkeypatch)
    output_dir = tmp_path / ".artifacts"
    _ = capsys.readouterr()
    (output_dir / "exec-check.exitcode.txt").unlink()

    exit_code = verify_main(["verify.py", str(contract_path)])
    captured = capsys.readouterr()
    result_payload = json.loads((output_dir / "verify_result.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert captured.out.strip() == "FAIL"
    assert result_payload["status"] == "FAIL"
    assert result_payload["reasons"] == ["missing evidence file for exec-check: exec-check.exitcode.txt"]


def test_verify_executes_black_box_condition_independently(tmp_path, capsys, monkeypatch) -> None:
    contract_path = prepare_workspace(tmp_path, monkeypatch)
    output_dir = tmp_path / ".artifacts"
    _ = capsys.readouterr()
    write_file(tmp_path / "probe.txt", "SECOND\n")

    exit_code = verify_main(["verify.py", str(contract_path)])
    captured = capsys.readouterr()
    result_payload = json.loads((output_dir / "verify_result.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.out.strip() == "PASS"
    assert result_payload["status"] == "PASS"
    assert (output_dir / "verify" / "black-box.stdout.txt").read_text(encoding="utf-8").strip() == "SECOND"
