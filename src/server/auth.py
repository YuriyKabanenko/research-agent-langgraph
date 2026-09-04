import hashlib
import secrets


def generate_token() -> str:
    """A high-entropy opaque bearer token - shown to the caller exactly once."""
    return secrets.token_urlsafe(32)


def hash_string(token: str) -> str:
    """One-way digest stored in the DB in place of the plaintext token.

    Plain SHA-256 (not a slow KDF like bcrypt) is fine here: the input is already
    256 bits of server-generated randomness, not a human-chosen password, so there's
    nothing for a slow hash to protect against that a fast, indexable digest doesn't.
    """
    return hashlib.sha256(token.encode()).hexdigest()