import pytest

from experiment.results_schema import make_result_record


def test_make_result_record_valid():
    result = {
        "ledger": {
            "E_driver": 1,
            "E_load": 2.5,
            "E_R": "3.0",
            "E_rad": 4,
            "E_parasitic": 5.25,
            "E_stored_t0": 6,
            "E_stored_t1": 7.75,
        },
        "residual": "0.5",
        "label": "CLOSED",
    }

    record = make_result_record(result)

    assert set(record) == {"ledger", "residual", "label"}
    assert set(record["ledger"]) == {
        "E_driver",
        "E_load",
        "E_R",
        "E_rad",
        "E_parasitic",
        "E_stored_t0",
        "E_stored_t1",
    }
    assert record["ledger"] == {
        "E_driver": 1.0,
        "E_load": 2.5,
        "E_R": 3.0,
        "E_rad": 4.0,
        "E_parasitic": 5.25,
        "E_stored_t0": 6.0,
        "E_stored_t1": 7.75,
    }
    assert record["residual"] == 0.5
    assert record["label"] == "CLOSED"


def test_make_result_record_invalid_raises():
    valid_ledger = {
        "E_driver": 1,
        "E_load": 2,
        "E_R": 3,
        "E_rad": 4,
        "E_parasitic": 5,
        "E_stored_t0": 6,
        "E_stored_t1": 7,
    }

    with pytest.raises(ValueError):
        make_result_record(
            {"ledger": valid_ledger, "residual": 0.0, "label": "OPEN"}
        )

    with pytest.raises(ValueError):
        make_result_record(
            {
                "ledger": {
                    "E_driver": 1,
                    "E_load": 2,
                    "E_R": 3,
                    "E_rad": 4,
                    "E_parasitic": 5,
                    "E_stored_t0": 6,
                },
                "residual": 0.0,
                "label": "CLOSED",
            }
        )

    with pytest.raises(ValueError):
        make_result_record(
            {"ledger": valid_ledger, "residual": float("inf"), "label": "CLOSED"}
        )
