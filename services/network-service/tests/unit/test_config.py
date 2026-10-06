import pytest
from pydantic import ValidationError

from network_service.config import Settings

VALID = {
    "database_url": "postgresql+psycopg://u:p@db:5432/d",
    "coordinator_api_key": "coordinator-key-abcdef",
    "operator_api_key": "operator-key-abcdefgh",
    "internal_api_key": "internal-key-abcdefgh",
}


def test_valid_settings_are_accepted() -> None:
    settings = Settings(**VALID)  # type: ignore[arg-type]

    assert settings.operator_api_key.get_secret_value() == VALID["operator_api_key"]


def test_secrets_are_not_shown_in_repr() -> None:
    settings = Settings(**VALID)  # type: ignore[arg-type]

    assert VALID["coordinator_api_key"] not in repr(settings)


@pytest.mark.parametrize(
    ("value", "reason"),
    [("CHANGE_ME_coordinator_key", "valor de ejemplo"), ("short", "al menos 16")],
)
def test_weak_api_keys_are_rejected(value: str, reason: str) -> None:
    with pytest.raises(ValidationError, match=reason):
        Settings(**{**VALID, "coordinator_api_key": value})  # type: ignore[arg-type]


def test_roles_must_have_distinct_keys() -> None:
    with pytest.raises(ValidationError, match="distinta"):
        Settings(**{**VALID, "operator_api_key": VALID["coordinator_api_key"]})  # type: ignore[arg-type]
