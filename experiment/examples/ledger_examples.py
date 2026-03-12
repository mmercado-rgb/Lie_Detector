from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiment.energy_ledger import classify_run, compute_residual, compute_stored_energy, integrate_power


TAU = 1e-9


def print_scenario(name: str, ledger: dict[str, float]) -> None:
    residual = compute_residual(ledger)
    label = classify_run(ledger, TAU)
    print(f"{name}: residual={residual}, label={label}")


def main() -> None:
    stored_energy = compute_stored_energy(
        {
            "L": [1.0],
            "i_L": [2.0],
            "C": [1.0],
            "v_C": [3.0],
        }
    )
    print(f"stored_energy_example: {stored_energy}")

    integrated_energy = integrate_power(
        {
            "v": [1.0, 1.0, 1.0],
            "i": [2.0, 2.0, 2.0],
            "t": [0.0, 1.0, 2.0],
        }
    )
    print(f"integrate_power_example: {integrated_energy}")

    print_scenario(
        "Scenario1_closed_system",
        {
            "E_driver": 10.0,
            "E_load": 7.0,
            "E_R": 2.0,
            "E_rad": 0.5,
            "E_parasitic": 0.5,
            "E_stored_t0": 1.0,
            "E_stored_t1": 1.0,
        },
    )
    print_scenario(
        "Scenario2_underaccounted",
        {
            "E_driver": 10.0,
            "E_load": 6.0,
            "E_R": 2.0,
            "E_rad": 0.5,
            "E_parasitic": 0.5,
            "E_stored_t0": 1.0,
            "E_stored_t1": 1.0,
        },
    )
    print_scenario(
        "Scenario3_apparent_excess",
        {
            "E_driver": 10.0,
            "E_load": 8.0,
            "E_R": 2.0,
            "E_rad": 1.0,
            "E_parasitic": 0.5,
            "E_stored_t0": 1.0,
            "E_stored_t1": 1.0,
        },
    )


if __name__ == "__main__":
    main()
