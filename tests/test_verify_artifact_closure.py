from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts" / "preflight.py"
RUN_AGENT = ROOT / "scripts" / "run_agent.py"
VERIFY = ROOT / "scripts" / "verify.py"
PYTHON = Path(sys.executable).as_posix()


WORKSPACE_CONTRACT = {
    "version": 2,
    "task_id": "exp-unauthorized-artifact",
    "goal": "Minimal verify injection test",
    "inputs": {
        "repo_root": ".",
        "allowed_paths": ["src/**", "tests/**", "scripts/**"],
    },
    "success_conditions": [
        {
            "id": "echo-ok",
            "type": "command_stdout_contains",
            "command": f"{PYTHON} -c \"print('HELLO')\"",
            "contains": "HELLO",
        }
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
        "require_black_box_verification": False,
        "reserved_outcome_words": ["PASS", "FAIL"],
    },
}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_preflight_accepts_valid_contract(tmp_path: Path) -> None:
    contract_path = tmp_path / "workspace.success.json"
    contract_path.write_text(json.dumps(WORKSPACE_CONTRACT, indent=2) + "\n", encoding="utf-8")

    result = run([sys.executable, str(PREFLIGHT), str(contract_path)], cwd=ROOT)
    output = result.stdout + "\n" + result.stderr

    assert result.returncode == 0, output


def test_verify_passes_on_clean_artifacts(tmp_path: Path) -> None:
    contract_path = tmp_path / "workspace.success.json"
    contract_path.write_text(json.dumps(WORKSPACE_CONTRACT, indent=2) + "\n", encoding="utf-8")

    run_agent = run([sys.executable, str(RUN_AGENT), str(contract_path)], cwd=ROOT)
    run_agent_out = run_agent.stdout + "\n" + run_agent.stderr
    assert run_agent.returncode == 0, run_agent_out

    baseline = run([sys.executable, str(VERIFY), str(contract_path)], cwd=ROOT)
    baseline_out = baseline.stdout + "\n" + baseline.stderr
    assert baseline.returncode == 0, baseline_out
    assert "PASS" in baseline_out, baseline_out


def test_verify_fails_on_extra_artifact(tmp_path: Path) -> None:
    contract_path = tmp_path / "workspace.success.json"
    contract_path.write_text(json.dumps(WORKSPACE_CONTRACT, indent=2) + "\n", encoding="utf-8")

    run_agent = run([sys.executable, str(RUN_AGENT), str(contract_path)], cwd=ROOT)
    run_agent_out = run_agent.stdout + "\n" + run_agent.stderr
    assert run_agent.returncode == 0, run_agent_out

    baseline = run([sys.executable, str(VERIFY), str(contract_path)], cwd=ROOT)
    baseline_out = baseline.stdout + "\n" + baseline.stderr
    assert baseline.returncode == 0, baseline_out
    assert "PASS" in baseline_out, baseline_out

    artifacts_dir = tmp_path / ".artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    (artifacts_dir / "unauthorized.txt").write_text("unauthorized\n", encoding="utf-8")

    injected = run([sys.executable, str(VERIFY), str(contract_path)], cwd=ROOT)
    injected_out = injected.stdout + "\n" + injected.stderr

    assert injected.returncode != 0, injected_out
    assert "FAIL" in injected_out, injected_out


def test_verify_fails_when_indexed_artifact_missing(tmp_path: Path) -> None:
    contract_path = tmp_path / "workspace.success.json"
    contract_path.write_text(json.dumps(WORKSPACE_CONTRACT, indent=2) + "\n", encoding="utf-8")

    run_agent = run([sys.executable, str(RUN_AGENT), str(contract_path)], cwd=ROOT)
    run_agent_out = run_agent.stdout + "\n" + run_agent.stderr
    assert run_agent.returncode == 0, run_agent_out

    artifacts_dir = tmp_path / ".artifacts"
    candidates = [p for p in artifacts_dir.rglob("*") if p.is_file() and p.name != "verify_result.json"]
    assert candidates, "No artifact files found to remove"

    candidates[0].unlink()

    result = run([sys.executable, str(VERIFY), str(contract_path)], cwd=ROOT)
    output = result.stdout + "\n" + result.stderr

    assert result.returncode != 0, output
    assert "FAIL" in output, output

    
