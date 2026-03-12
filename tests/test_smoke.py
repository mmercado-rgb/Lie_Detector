from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_smoke_outputs_expected_experiment_markers() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "smoke.py")],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    stdout = result.stdout
    assert "stored_energy_example: 6.5" in stdout
    assert "integrate_power_example: 4.0" in stdout
    assert "closed_system: residual=0.0, label=CLOSED" in stdout
    assert "underaccounted_energy: residual=1.0, label=UNDERACCOUNTED" in stdout
    assert "apparent_excess_energy: residual=-1.0, label=APPARENT_EXCESS" in stdout
    assert "batch_runner_closed: count=1, label=CLOSED" in stdout
    assert (
        "analyze_runs_mixed: total_runs=3, count_closed=1, "
        "count_underaccounted=1, count_apparent_excess=1"
    ) in stdout
    assert "smoke_complete" in stdout
