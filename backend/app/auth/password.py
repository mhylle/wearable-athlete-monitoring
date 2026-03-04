"""Password hashing and verification using Argon2 via pwdlib."""

from pwdlib import PasswordHash

_hasher = PasswordHash.recommended()


def hash_password(plain: str) -> str:
    """Hash a plaintext password using Argon2."""
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a hash."""
    return _hasher.verify(plain, hashed)
