"""Tests for password hashing and verification."""

from app.auth.password import hash_password, verify_password


class TestPasswordHashing:
    """Test Argon2 password hashing."""

    def test_hash_creates_string(self) -> None:
        hashed = hash_password("mysecret")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_is_not_plaintext(self) -> None:
        hashed = hash_password("mysecret")
        assert hashed != "mysecret"

    def test_verify_correct_password(self) -> None:
        hashed = hash_password("mysecret")
        assert verify_password("mysecret", hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = hash_password("mysecret")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self) -> None:
        h1 = hash_password("mysecret")
        h2 = hash_password("mysecret")
        assert h1 != h2  # Different salts

    def test_empty_password_hashes(self) -> None:
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False
