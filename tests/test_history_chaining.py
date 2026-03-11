from __future__ import annotations

import json

from scripts.run_agent import main as run_agent_main
from scripts.verify import main as verify_main
from tests.helpers import build_sample_workspace, write_contract, write_file


def prepare_chain_workspace(tmp_path, monkeypatch):
    build_sample_workspace(tmp_path)
    contract_path = write_contract(
        tmp_path,
        require_black_box_verification=False,
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
        ],
    )
    monkeypatch.chdir(tmp_path)
    return contract_path


def load_manifest(tmp_path):
    return json.loads((tmp_path / ".artifacts" / "execution_manifest.json").read_text(encoding="utf-8"))


def load_evidence_index(tmp_path):
    return json.loads((tmp_path / ".artifacts" / "evidence_index.json").read_text(encoding="utf-8"))


def load_verify_result(tmp_path):
    return json.loads((tmp_path / ".artifacts" / "verify_result.json").read_text(encoding="utf-8"))


def latest_run_id_path(tmp_path):
    return tmp_path / ".truth" / "latest_run_id.txt"


def test_first_run_writes_chain_fields_and_passes(tmp_path, capsys, monkeypatch) -> None:
    contract_path = prepare_chain_workspace(tmp_path, monkeypatch)

    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()

    manifest = load_manifest(tmp_path)
    evidence_index = load_evidence_index(tmp_path)
    assert manifest["previous_run_id"] is None
    assert evidence_index["previous_run_id"] is None
    assert manifest["run_id"] == evidence_index["run_id"]
    assert not latest_run_id_path(tmp_path).exists()

    assert verify_main(["verify.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    assert latest_run_id_path(tmp_path).read_text(encoding="utf-8").strip() == manifest["run_id"]


def test_second_valid_run_links_to_last_verified_run_and_passes(tmp_path, capsys, monkeypatch) -> None:
    contract_path = prepare_chain_workspace(tmp_path, monkeypatch)

    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    first_manifest = load_manifest(tmp_path)
    first_run_id = first_manifest["run_id"]
    assert verify_main(["verify.py", str(contract_path)]) == 0
    _ = capsys.readouterr()

    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    second_manifest = load_manifest(tmp_path)
    second_index = load_evidence_index(tmp_path)

    assert second_manifest["run_id"] != first_run_id
    assert second_manifest["previous_run_id"] == first_run_id
    assert second_index["previous_run_id"] == first_run_id

    assert verify_main(["verify.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    assert latest_run_id_path(tmp_path).read_text(encoding="utf-8").strip() == second_manifest["run_id"]


def test_missing_prior_run_state_fails_closed(tmp_path, capsys, monkeypatch) -> None:
    contract_path = prepare_chain_workspace(tmp_path, monkeypatch)

    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    assert verify_main(["verify.py", str(contract_path)]) == 0
    _ = capsys.readouterr()

    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    latest_run_id_path(tmp_path).unlink()

    assert verify_main(["verify.py", str(contract_path)]) == 1
    _ = capsys.readouterr()
    assert load_verify_result(tmp_path)["reasons"] == ["a prior run is required but missing"]


def test_failed_verification_does_not_advance_latest_run_id(tmp_path, capsys, monkeypatch) -> None:
    contract_path = prepare_chain_workspace(tmp_path, monkeypatch)

    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    first_run_id = load_manifest(tmp_path)["run_id"]
    assert verify_main(["verify.py", str(contract_path)]) == 0
    _ = capsys.readouterr()

    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    write_file(tmp_path / ".artifacts" / "exec-check.stdout.txt", "BROKEN\n")

    assert verify_main(["verify.py", str(contract_path)]) == 1
    _ = capsys.readouterr()
    assert latest_run_id_path(tmp_path).read_text(encoding="utf-8").strip() == first_run_id


def test_malformed_continuity_state_fails_closed(tmp_path, capsys, monkeypatch) -> None:
    contract_path = prepare_chain_workspace(tmp_path, monkeypatch)

    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    assert verify_main(["verify.py", str(contract_path)]) == 0
    _ = capsys.readouterr()

    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    write_file(latest_run_id_path(tmp_path), "not-a-run-id\n")

    assert verify_main(["verify.py", str(contract_path)]) == 1
    _ = capsys.readouterr()
    assert load_verify_result(tmp_path)["reasons"] == ["continuity state is malformed"]


def test_run_id_changes_every_run(tmp_path, capsys, monkeypatch) -> None:
    contract_path = prepare_chain_workspace(tmp_path, monkeypatch)

    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    first_run_id = load_manifest(tmp_path)["run_id"]
    assert verify_main(["verify.py", str(contract_path)]) == 0
    _ = capsys.readouterr()

    assert run_agent_main(["run_agent.py", str(contract_path)]) == 0
    _ = capsys.readouterr()
    second_run_id = load_manifest(tmp_path)["run_id"]

    assert second_run_id != first_run_id
