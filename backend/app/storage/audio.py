"""Ephemeral, encrypted audio storage.

Audio is encrypted in the application (AES-256-GCM) before it reaches object storage, so
confidentiality does not depend on the storage provider. Objects live only until processing
finishes; a 1-day bucket expiry rule is the backstop. V1 has no retention option by design;
clinician-approved retention would be a new policy on this class, not a new code path.
"""

import asyncio
import base64
import os
import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

import boto3
from botocore.config import Config
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings

_FORMAT = b"v1"  # key/format version, enables key rotation


class ObjectStore(Protocol):
    def put(self, key: str, data: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...


class S3ObjectStore:
    def __init__(self) -> None:
        s = get_settings()
        self.bucket = s.s3_bucket_audio
        self.client = boto3.client(
            "s3",
            endpoint_url=s.s3_endpoint_url,
            region_name=s.s3_region,
            aws_access_key_id=s.s3_access_key,
            aws_secret_access_key=s.s3_secret_key.get_secret_value(),
            config=Config(connect_timeout=3, read_timeout=10, retries={"max_attempts": 2}),
        )

    def put(self, key: str, data: bytes) -> None:
        self.client.put_object(
            Bucket=self.bucket, Key=key, Body=data, ContentType="application/octet-stream"
        )

    def get(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except self.client.exceptions.ClientError:
            return False


@dataclass
class EphemeralAudioStore:
    store: ObjectStore
    key: bytes

    def _aead(self) -> AESGCM:
        return AESGCM(self.key)

    async def put(self, audio: bytes) -> str:
        object_key = f"audio/{uuid.uuid4()}"
        nonce = os.urandom(12)
        blob = _FORMAT + nonce + self._aead().encrypt(nonce, audio, object_key.encode())
        await asyncio.to_thread(self.store.put, object_key, blob)
        return object_key

    async def get(self, object_key: str) -> bytes:
        blob = await asyncio.to_thread(self.store.get, object_key)
        if blob[:2] != _FORMAT:
            raise ValueError("unknown audio format")
        # Associated data binds the ciphertext to its object key (no swapping objects).
        return self._aead().decrypt(blob[2:14], blob[14:], object_key.encode())

    async def delete(self, object_key: str) -> None:
        await asyncio.to_thread(self.store.delete, object_key)

    async def exists(self, object_key: str) -> bool:
        return await asyncio.to_thread(self.store.exists, object_key)


@lru_cache
def get_audio_store() -> EphemeralAudioStore:
    key = base64.b64decode(get_settings().audio_encryption_key.get_secret_value())
    if len(key) != 32:
        raise ValueError("AUDIO_ENCRYPTION_KEY must be 32 bytes (base64)")
    return EphemeralAudioStore(S3ObjectStore(), key)
