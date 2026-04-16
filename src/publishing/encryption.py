"""AES-256-GCM encryption helpers for platform credential storage.

Security notes:
- Fixed application salt with HKDF means all rows under the same key_version
  share the same AES key. Per-row uniqueness comes from the random 12-byte nonce.
  Safe for AES-256-GCM up to ~2^32 encryptions (well within our scale).
- Never log decrypted credentials or include them in error messages.
"""

from __future__ import annotations

import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from .exceptions import CredentialError

_NONCE_SIZE = 12
_KEY_SIZE = 32
_HKDF_SALT = b"clair-publishing-credential-encryption-v1"
_HKDF_INFO = b"aes-256-gcm-key"


def derive_key(secret: str) -> bytes:
    """Derive a 32-byte AES-256 key from a master secret via HKDF-SHA256.

    A new HKDF instance is created each call (HKDF is single-use).
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=_KEY_SIZE,
        salt=_HKDF_SALT,
        info=_HKDF_INFO,
    )
    return hkdf.derive(secret.encode("utf-8"))


def encrypt_token(plaintext: str, key: bytes) -> bytes:
    """Encrypt a plaintext string with AES-256-GCM.

    Returns nonce (12 bytes) + ciphertext+tag as a single bytes blob.
    """
    nonce = os.urandom(_NONCE_SIZE)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ct


def decrypt_token(data: bytes, key: bytes) -> str:
    """Decrypt AES-256-GCM ciphertext produced by encrypt_token().

    Raises CredentialError on decryption failure.
    """
    if len(data) < _NONCE_SIZE + 16:  # nonce + minimum tag
        raise CredentialError("Encrypted data too short")
    nonce = data[:_NONCE_SIZE]
    ct = data[_NONCE_SIZE:]
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ct, None)
    except Exception as e:
        raise CredentialError("Credential decryption failed") from e
    return plaintext.decode("utf-8")
