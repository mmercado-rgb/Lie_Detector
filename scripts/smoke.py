from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.app import get_status_message  # noqa: E402


def main() -> int:
    print(get_status_message())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
