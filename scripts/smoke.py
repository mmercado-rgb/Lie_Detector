from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    report_path = REPO_ROOT / "output" / "report.txt"
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "src" / "report_generator.py")],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    report_exists = report_path.exists()
    report_contains_marker = False
    if report_exists:
        report_contains_marker = "REPORT_OK" in report_path.read_text(encoding="utf-8")
    if result.returncode == 0 and result.stdout.strip() == "Report generated" and report_exists and report_contains_marker:
        print("OK")
        return 0
    print("FAIL")
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
