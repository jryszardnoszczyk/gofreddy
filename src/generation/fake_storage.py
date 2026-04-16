"""Local in-memory asset backend for fake video generation flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FakeStoredAsset:
    data: bytes
    content_type: str


class _FakeStreamingBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    async def read(self) -> bytes:
        return self._data


class _FakeS3Client:
    def __init__(self, backend: "FakeGenerationAssetStorage") -> None:
        self._backend = backend

    async def put_object(
        self,
        *,
        Bucket: str,  # noqa: N803
        Key: str,  # noqa: N803
        Body: bytes,  # noqa: N803
        ContentType: str,  # noqa: N803
    ) -> None:
        self._backend.put_asset(Key, Body, ContentType)

    async def generate_presigned_url(
        self,
        operation_name: str,
        *,
        Params: dict[str, Any],  # noqa: N803
        ExpiresIn: int,  # noqa: N803
    ) -> str:
        if operation_name != "get_object":
            raise ValueError(f"Unsupported fake operation: {operation_name}")
        key = Params["Key"]
        return self._backend.asset_url(key)

    async def list_objects_v2(
        self,
        *,
        Bucket: str,  # noqa: N803
        Prefix: str,  # noqa: N803
        MaxKeys: int,  # noqa: N803
    ) -> dict[str, list[dict[str, str]]]:
        keys = self._backend.list_keys(Prefix)[:MaxKeys]
        return {"Contents": [{"Key": key} for key in keys]}

    async def delete_object(
        self,
        *,
        Bucket: str,  # noqa: N803
        Key: str,  # noqa: N803
    ) -> None:
        self._backend.delete_asset(Key)

    async def get_object(
        self,
        *,
        Bucket: str,  # noqa: N803
        Key: str,  # noqa: N803
    ) -> dict[str, _FakeStreamingBody]:
        asset = self._backend.get_asset(Key)
        if asset is None:
            raise FileNotFoundError(Key)
        return {"Body": _FakeStreamingBody(asset.data)}


class FakeGenerationAssetStorage:
    """Minimal S3-compatible backend used by fake generation storage."""

    def __init__(self, public_base_url: str) -> None:
        self._public_base_url = public_base_url.rstrip("/")
        self._client = _FakeS3Client(self)
        self._assets: dict[str, FakeStoredAsset] = {}

    async def _get_client(self) -> _FakeS3Client:
        return self._client

    def put_asset(self, key: str, data: bytes, content_type: str) -> None:
        self._assets[key] = FakeStoredAsset(data=data, content_type=content_type)

    def get_asset(self, key: str) -> FakeStoredAsset | None:
        return self._assets.get(key)

    def delete_asset(self, key: str) -> None:
        self._assets.pop(key, None)

    def list_keys(self, prefix: str) -> list[str]:
        return sorted(key for key in self._assets if key.startswith(prefix))

    def asset_url(self, key: str) -> str:
        return f"{self._public_base_url}/v1/generation/assets/{key}"
