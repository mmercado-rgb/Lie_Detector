from __future__ import annotations

import hashlib
import json
import shutil

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


def test_verify_baseline_pass(tmp_path, capsys, monkeypatch) -> None:
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


def test_verify_fails_on_injected_extra_artifact_file(tmp_path, capsys, monkeypatch) -> None:
    contract_path = prepare_workspace(tmp_path, monkeypatch)
    output_dir = tmp_path / ".artifacts"
    _ = capsys.readouterr()
    write_file(tmp_path / "probe.txt", "SECOND\n")
    assert verify_main(["verify.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    write_file(output_dir / "unauthorized.txt", "injected\n")

    exit_code = verify_main(["verify.py", str(contract_path)])
    captured = capsys.readouterr()
    result_payload = json.loads((output_dir / "verify_result.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert captured.out.strip() == "FAIL"
    assert result_payload["status"] == "FAIL"
    assert result_payload["reasons"] == ["unexpected artifact files on disk: unauthorized.txt"]


def test_verify_allowlisted_verifier_files_do_not_fail_inventory(tmp_path, capsys, monkeypatch) -> None:
    contract_path = prepare_workspace(tmp_path, monkeypatch)
    output_dir = tmp_path / ".artifacts"
    _ = capsys.readouterr()
    write_file(tmp_path / "probe.txt", "SECOND\n")

    first_exit_code = verify_main(["verify.py", str(contract_path)])
    _ = capsys.readouterr()
    assert first_exit_code == 0
    assert (output_dir / "verify_result.json").exists()
    assert (output_dir / "verify" / "black-box.stdout.txt").exists()

    second_exit_code = verify_main(["verify.py", str(contract_path)])
    second_output = capsys.readouterr()
    second_payload = json.loads((output_dir / "verify_result.json").read_text(encoding="utf-8"))

    assert second_exit_code == 0
    assert second_output.out.strip() == "PASS"
    assert second_payload["status"] == "PASS"


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


def test_verify_fails_on_replayed_artifacts_bundle(tmp_path, capsys, monkeypatch) -> None:
    build_sample_workspace(tmp_path)
    write_file(tmp_path / "probe.txt", "RUN_A\n")
    contract_path = write_contract(
        tmp_path,
        require_black_box_verification=False,
        success_conditions=[
            {
                "id": "exec-check",
                "type": "command_stdout_contains",
                "command": "python -c \"from pathlib import Path; print(Path('probe.txt').read_text(encoding='utf-8').strip())\"",
                "contains": "RUN_A",
            },
            {
                "id": "required-file",
                "type": "file_exists",
                "path": "src/app.py",
            },
        ],
    )

    monkeypatch.chdir(tmp_path)
    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    assert verify_main(["verify.py", str(contract_path)]) == 0
    _ = capsys.readouterr()

    output_dir = tmp_path / ".artifacts"
    replay_bundle = tmp_path / ".artifacts_run_a"
    shutil.copytree(output_dir, replay_bundle)

    write_file(tmp_path / "probe.txt", "RUN_B\n")
    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    assert verify_main(["verify.py", str(contract_path)]) == 1
    _ = capsys.readouterr()

    shutil.rmtree(output_dir)
    shutil.copytree(replay_bundle, output_dir)

    exit_code = verify_main(["verify.py", str(contract_path)])
    captured = capsys.readouterr()
    result_payload = json.loads((output_dir / "verify_result.json").read_text(encoding="utf-8"))

    assert exit_code == 1
    assert captured.out.strip() == "FAIL"
    assert result_payload["status"] == "FAIL"
    assert result_payload["reasons"] == ["evidence run_id does not match freshness marker"]

def test_verify_fails_on_undeclared_extra_artifact(tmp_path, capsys, monkeypatch) -> None:
    build_sample_workspace(tmp_path)
    contract_path = write_contract(
        tmp_path,
        success_conditions=[
            {
                "id": "exec-check",
                "type": "command_stdout_contains",
                "command": 'python -c "print(\'ALPHA\')"',
                "contains": "ALPHA",
            }
        ],
        require_black_box_verification=False,
    )

    monkeypatch.chdir(tmp_path)
    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()

    write_file(tmp_path / ".artifacts" / "unexpected.txt", "x\n")

    from scripts.verify import main as verify_main
    exit_code = verify_main(["verify.py", str(contract_path)])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "FAIL" in captured.out

def test_verify_fails_if_contract_changes_after_run(tmp_path, capsys, monkeypatch) -> None:
    build_sample_workspace(tmp_path)
    contract_path = write_contract(
        tmp_path,
        success_conditions=[
            {
                "id": "exec-check",
                "type": "command_stdout_contains",
                "command": 'python -c "print(\'ALPHA\')"',
                "contains": "ALPHA",
            }
        ],
        require_black_box_verification=False,
    )

    monkeypatch.chdir(tmp_path)
    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()

    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    payload["goal"] = "mutated after execution"
    write_file(contract_path, json.dumps(payload, indent=2) + "\n")

    from scripts.verify import main as verify_main
    exit_code = verify_main(["verify.py", str(contract_path)])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "FAIL" in captured.out
