from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)


def test_password_hash_and_verify():
    hashed = hash_password("secret123")

    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_token_roundtrip():
    token = create_access_token(manager_id=42)

    assert verify_token(token) == 42