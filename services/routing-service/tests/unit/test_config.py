import pytest
from pydantic import ValidationError

from routing_service.config import Settings

VALID = {
    "network_service_url": "http://network-service:8001",
    "coordinator_api_key": "coordinator-key-abcdef",
    "operator_api_key": "operator-key-abcdefgh",
    "internal_api_key": "internal-key-abcdefgh",
}


def test_valid_settings_are_accepted() -> None:
    settings = Settings(**VALID)  # type: ignore[arg-type]

    assert str(settings.network_service_url).startswith("http://network-service:8001")


@pytest.mark.parametrize(
    ("value", "reason"),
    [("CHANGE_ME_operator_key", "valor de ejemplo"), ("short", "al menos 16")],
)
def test_weak_api_keys_are_rejected(value: str, reason: str) -> None:
    with pytest.raises(ValidationError, match=reason):
        Settings(**{**VALID, "operator_api_key": value})  # type: ignore[arg-type]


def test_roles_must_have_distinct_keys() -> None:
    with pytest.raises(ValidationError, match="distinta"):
        Settings(**{**VALID, "internal_api_key": VALID["operator_api_key"]})  # type: ignore[arg-type]


def test_network_service_url_must_be_a_url() -> None:
    with pytest.raises(ValidationError):
        Settings(**{**VALID, "network_service_url": "no-es-url"})  # type: ignore[arg-type]
