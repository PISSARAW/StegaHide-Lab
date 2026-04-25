"""Tests for the encryption helpers."""

import pytest

from steganography.encryption import decrypt_message, encrypt_message, generate_key


class TestGenerateKey:
    def test_returns_string(self):
        key = generate_key()
        assert isinstance(key, str)

    def test_key_is_non_empty(self):
        assert generate_key() != ""

    def test_keys_are_unique(self):
        assert generate_key() != generate_key()


class TestEncryptDecrypt:
    def test_round_trip(self):
        key = generate_key()
        plaintext = "secret message"
        ciphertext = encrypt_message(plaintext, key)
        assert decrypt_message(ciphertext, key) == plaintext

    def test_ciphertext_differs_from_plaintext(self):
        key = generate_key()
        plaintext = "secret message"
        ciphertext = encrypt_message(plaintext, key)
        assert ciphertext != plaintext

    def test_same_plaintext_produces_different_ciphertexts(self):
        """Fernet uses a random IV so ciphertexts should differ."""
        key = generate_key()
        plaintext = "hello"
        ct1 = encrypt_message(plaintext, key)
        ct2 = encrypt_message(plaintext, key)
        assert ct1 != ct2

    def test_empty_string_round_trip(self):
        key = generate_key()
        ct = encrypt_message("", key)
        assert decrypt_message(ct, key) == ""

    def test_unicode_round_trip(self):
        key = generate_key()
        plaintext = "こんにちは 🌐"
        ct = encrypt_message(plaintext, key)
        assert decrypt_message(ct, key) == plaintext

    def test_decrypt_with_wrong_key_raises(self):
        key1 = generate_key()
        key2 = generate_key()
        ct = encrypt_message("secret", key1)
        with pytest.raises(ValueError, match="[Dd]ecrypt"):
            decrypt_message(ct, key2)

    def test_encrypt_with_invalid_key_raises(self):
        with pytest.raises(ValueError, match="[Ii]nvalid"):
            encrypt_message("hello", "not-a-valid-key")

    def test_decrypt_with_invalid_key_raises(self):
        key = generate_key()
        ct = encrypt_message("hello", key)
        with pytest.raises(ValueError):
            decrypt_message(ct, "bad-key")

    def test_decrypt_corrupted_ciphertext_raises(self):
        key = generate_key()
        with pytest.raises(ValueError):
            decrypt_message("this-is-not-valid-ciphertext", key)
