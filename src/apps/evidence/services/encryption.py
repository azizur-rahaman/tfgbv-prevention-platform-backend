import gzip
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


def get_master_key() -> bytes:
    """
    Retrieves the 32-byte AES master key from settings.
    NEVER hardcode this. It lives in .env only.
    """
    key_hex = settings.EVIDENCE_ENCRYPTION_KEY
    key_bytes = bytes.fromhex(key_hex)
    if len(key_bytes) != 32:
        raise ValueError("EVIDENCE_ENCRYPTION_KEY must be exactly 32 bytes (64 hex chars).")
    return key_bytes


def encrypt_file(raw_bytes: bytes) -> tuple[bytes, bytes]:
    """
    1. Compresses raw bytes with gzip
    2. Encrypts with AES-256-GCM

    Returns:
        encrypted_data (bytes)  — what gets stored in MinIO
        nonce (bytes)           — 12 bytes, store in Evidence.encryption_nonce
    """
    # Step 1: Compress
    compressed = gzip.compress(raw_bytes, compresslevel=9)

    # Step 2: Generate a random 12-byte nonce (unique per file)
    nonce = os.urandom(12)

    # Step 3: Encrypt
    aesgcm = AESGCM(get_master_key())
    encrypted = aesgcm.encrypt(nonce, compressed, None)

    return encrypted, nonce


def decrypt_file(encrypted_bytes: bytes, nonce: bytes) -> bytes:
    """
    Reverses the process: decrypts then decompresses.

    Returns the original raw bytes — identical to what was captured
    on the mobile device. Re-hashing this must match Evidence.file_hash.
    """
    aesgcm = AESGCM(get_master_key())

    # Step 1: Decrypt
    compressed = aesgcm.decrypt(nonce, encrypted_bytes, None)

    # Step 2: Decompress
    raw_bytes = gzip.decompress(compressed)

    return raw_bytes