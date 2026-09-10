import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken


@lru_cache
def _fernet() -> Fernet:
    # Cached rather than module-level: load_dotenv() runs in each entrypoint's own
    # module before server.main is imported, so the env var isn't reliably set yet
    # at import time - reading it lazily on first use avoids that ordering trap.
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY is not set. Generate one with "
            "`python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"` "
            "and add it to .env."
        )
    return Fernet(key.encode())


def encrypt_token(plain: str) -> str:
    """Encrypts a BYOK API token for storage. Reversible by design - unlike auth
    tokens (auth.py's hash_string), this has to be readable again to call the
    provider's API on the user's behalf."""
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError(
            "Failed to decrypt stored API token - ENCRYPTION_KEY may have changed since "
            "it was saved."
        ) from exc
