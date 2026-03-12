from __future__ import annotations

import pytest

from experiment.results_schema import make_result_record


def test_make_result_record_normalizes_values() -> None:
    result = {
        "ledger": {
            "E_driver": 5,
            "E_load": "3.0",
            "E_R": 1,
            "E_rad": 0.5,
            "E_parasitic": 0.5,
            "E_stored_t0": 0,
            "E_stored_t1": 0,
        },
        "residual": "0.0",
        "label": "CLOSED",
    }

    record = make_result_record(result)

    assert list(record.keys()) == ["ledger", "residual", "label"]
    assert record["ledger"] == {
        "E_driver": 5.0,
        "E_load": 3.0,
        "E_R": 1.0,
        "E_rad": 0.5,
        "E_parasitic": 0.5,
        "E_stored_t0": 0.0,
        "E_stored_t1": 0.0,
    }
    assert record["residual"] == 0.0
    assert record["label"] == "CLOSED"


def test_make_result_record_rejects_invalid_result() -> None:
    with pytest.raises(ValueError):
        make_result_record(
            {
                "ledger": {
                    "E_driver": 1.0,
                    "E_load": 1.0,
                    "E_R": 1.0,
                    "E_rad": 1.0,
                    "E_parasitic": 1.0,
                    "E_stored_t0": 1.0,
                },
                "residual": 0.0,
                "label": "CLOSED",
            }
        )

    with pytest.raises(ValueError):
        make_result_record(
            {
                "ledger": {
                    "E_driver": 1.0,
                    "E_load": 1.0,
                    "E_R": 1.0,
                    "E_rad": 1.0,
                    "E_parasitic": 1.0,
                    "E_stored_t0": 1.0,
                    "E_stored_t1": 1.0,
                },
                "residual": float("inf"),
                "label": "CLOSED",
            }
        )

    with pytest.raises(ValueError):
        make_result_record(
            {
                "ledger": {
                    "E_driver": 1.0,
                    "E_load": 1.0,
                    "E_R": 1.0,
                    "E_rad": 1.0,
                    "E_parasitic": 1.0,
                    "E_stored_t0": 1.0,
                    "E_stored_t1": 1.0,
                },
                "residual": 0.0,
                "label": "UNKNOWN",
            }
        )
