"""
encryption.py – symmetric encryption helpers using the Fernet scheme.

Messages can optionally be encrypted before being embedded in an image.  The
same key must be supplied during decryption.

Fernet guarantees:
    • AES-128 in CBC mode for confidentiality.
    • HMAC-SHA256 for authenticity / integrity.
    • A random IV per encryption → identical plaintexts produce different
      ciphertexts.

Usage example::

    from steganography.encryption import generate_key, encrypt_message, decrypt_message

    key = generate_key()
    cipher = encrypt_message("top secret", key)
    plain  = decrypt_message(cipher, key)
    assert plain == "top secret"
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


def generate_key() -> str:
    """Generate and return a new URL-safe base64-encoded Fernet key (string)."""
    return Fernet.generate_key().decode("utf-8")


def encrypt_message(message: str, key: str) -> str:
    """Encrypt *message* with *key* and return the ciphertext as a string.

    Parameters
    ----------
    message:
        Plaintext to encrypt.
    key:
        Fernet key produced by :func:`generate_key`.

    Returns
    -------
    str
        URL-safe base64-encoded ciphertext (safe to embed in an image as text).

    Raises
    ------
    ValueError
        If *key* is not a valid Fernet key.
    """
    try:
        f = Fernet(key.encode("utf-8"))
    except (ValueError, Exception) as exc:
        raise ValueError(f"Invalid encryption key: {exc}") from exc

    token = f.encrypt(message.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_message(ciphertext: str, key: str) -> str:
    """Decrypt *ciphertext* with *key* and return the original plaintext.

    Parameters
    ----------
    ciphertext:
        Ciphertext produced by :func:`encrypt_message`.
    key:
        Fernet key used during encryption.

    Returns
    -------
    str
        Decrypted plaintext.

    Raises
    ------
    ValueError
        If *key* is invalid or *ciphertext* cannot be authenticated / decrypted.
    """
    try:
        f = Fernet(key.encode("utf-8"))
        plaintext = f.decrypt(ciphertext.encode("utf-8"))
    except InvalidToken as exc:
        raise ValueError(
            "Decryption failed: invalid key or corrupted ciphertext."
        ) from exc
    except (ValueError, Exception) as exc:
        raise ValueError(f"Decryption error: {exc}") from exc

    return plaintext.decode("utf-8")
