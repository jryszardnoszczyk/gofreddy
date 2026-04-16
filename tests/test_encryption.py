"""Tests for AES-256-GCM encryption helpers."""

import pytest

from src.publishing.encryption import decrypt_token, derive_key, encrypt_token
from src.publishing.exceptions import CredentialError


class TestDeriveKey:
    def test_deterministic(self):
        key1 = derive_key("my-secret")
        key2 = derive_key("my-secret")
        assert key1 == key2

    def test_different_secrets_different_keys(self):
        key1 = derive_key("secret-a")
        key2 = derive_key("secret-b")
        assert key1 != key2

    def test_key_length(self):
        key = derive_key("test-secret")
        assert len(key) == 32


class TestEncryptDecrypt:
    def test_round_trip(self):
        key = derive_key("test-secret")
        plaintext = "my-oauth-token-12345"
        encrypted = encrypt_token(plaintext, key)
        decrypted = decrypt_token(encrypted, key)
        assert decrypted == plaintext

    def test_empty_string(self):
        key = derive_key("test-secret")
        encrypted = encrypt_token("", key)
        decrypted = decrypt_token(encrypted, key)
        assert decrypted == ""

    def test_unicode_content(self):
        key = derive_key("test-secret")
        plaintext = '{"password": "zażółć gęślą jaźń"}'
        encrypted = encrypt_token(plaintext, key)
        decrypted = decrypt_token(encrypted, key)
        assert decrypted == plaintext

    def test_wrong_key_raises(self):
        key1 = derive_key("correct-secret")
        key2 = derive_key("wrong-secret")
        encrypted = encrypt_token("sensitive-data", key1)
        with pytest.raises(CredentialError, match="decryption failed"):
            decrypt_token(encrypted, key2)

    def test_truncated_data_raises(self):
        key = derive_key("test-secret")
        with pytest.raises(CredentialError, match="too short"):
            decrypt_token(b"short", key)

    def test_different_encryptions_differ(self):
        """Each encryption produces different ciphertext (random nonce)."""
        key = derive_key("test-secret")
        enc1 = encrypt_token("same-text", key)
        enc2 = encrypt_token("same-text", key)
        assert enc1 != enc2  # different nonces
