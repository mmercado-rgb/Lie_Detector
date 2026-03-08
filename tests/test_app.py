from src.app import get_status_message


def test_get_status_message() -> None:
    assert get_status_message() == "OK"
