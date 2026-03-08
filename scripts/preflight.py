from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.contract_model import load_contract  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("INVALID")
        return 2

    contract_path = Path(argv[1])
    try:
        _ = load_contract(contract_path)
    except ValueError:
        print("INVALID")
        return 1

    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
