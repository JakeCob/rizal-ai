"""Where rendered audio lives. Local for development (served by the API at
/audio), Supabase Storage in production (public bucket, CDN URLs)."""

from pathlib import Path
from typing import Protocol

import httpx


class AudioStore(Protocol):
    def exists(self, key: str) -> bool: ...
    def put(self, key: str, data: bytes, content_type: str) -> None: ...
    def url(self, key: str) -> str: ...


class LocalAudioStore:
    def __init__(self, directory: Path, base_url: str = "/audio") -> None:
        self._dir = directory
        self._base = base_url.rstrip("/")
        self._dir.mkdir(parents=True, exist_ok=True)

    def exists(self, key: str) -> bool:
        return (self._dir / key).is_file()

    def put(self, key: str, data: bytes, content_type: str) -> None:
        (self._dir / key).write_bytes(data)

    def url(self, key: str) -> str:
        return f"{self._base}/{key}"


class SupabaseAudioStore:
    """Supabase Storage through its REST API. The bucket must be public so
    the web app can play files by URL without a token."""

    def __init__(
        self,
        supabase_url: str,
        service_role_key: str,
        bucket: str = "audio",
        client: httpx.Client | None = None,
    ) -> None:
        self._base = supabase_url.rstrip("/")
        self._bucket = bucket
        self._client = client or httpx.Client(timeout=60.0)
        self._headers = {"Authorization": f"Bearer {service_role_key}", "apikey": service_role_key}

    def exists(self, key: str) -> bool:
        response = self._client.head(self.url(key))
        return response.status_code == 200

    def put(self, key: str, data: bytes, content_type: str) -> None:
        response = self._client.post(
            f"{self._base}/storage/v1/object/{self._bucket}/{key}",
            headers={**self._headers, "Content-Type": content_type, "x-upsert": "true"},
            content=data,
        )
        response.raise_for_status()

    def url(self, key: str) -> str:
        return f"{self._base}/storage/v1/object/public/{self._bucket}/{key}"
