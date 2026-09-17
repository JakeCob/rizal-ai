"""Where rendered audio lives: a local directory for development, an
S3-compatible bucket (Railway buckets) in production. Either way the web
app fetches audio from the API at /audio/{key}, so URLs never depend on the
store and the bucket needs no public access (DECISIONS.md D33)."""

import mimetypes
from pathlib import Path
from typing import Any, Protocol


class AudioStore(Protocol):
    def exists(self, key: str) -> bool: ...
    def put(self, key: str, data: bytes, content_type: str) -> None: ...
    def get(self, key: str) -> tuple[bytes, str] | None: ...
    def url(self, key: str) -> str: ...


CONTENT_TYPES = {".wav": "audio/wav", ".mp3": "audio/mpeg"}


def _content_type(key: str) -> str:
    for ext, content_type in CONTENT_TYPES.items():
        if key.endswith(ext):
            return content_type
    guessed, _ = mimetypes.guess_type(key)
    return guessed or "application/octet-stream"


class LocalAudioStore:
    def __init__(self, directory: Path, base_url: str = "/audio") -> None:
        self._dir = directory
        self._base = base_url.rstrip("/")
        self._dir.mkdir(parents=True, exist_ok=True)

    def exists(self, key: str) -> bool:
        return (self._dir / key).is_file()

    def put(self, key: str, data: bytes, content_type: str) -> None:
        (self._dir / key).write_bytes(data)

    def get(self, key: str) -> tuple[bytes, str] | None:
        path = self._dir / key
        if not path.is_file():
            return None
        return path.read_bytes(), _content_type(key)

    def url(self, key: str) -> str:
        return f"{self._base}/{key}"


class S3AudioStore:
    """Any S3-compatible bucket through boto3. Railway buckets expose an S3
    endpoint plus access keys; the same adapter works for R2 or AWS."""

    def __init__(self, client: Any, bucket: str, base_url: str) -> None:
        self._s3 = client
        self._bucket = bucket
        self._base = base_url.rstrip("/")

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._s3.head_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return False
            raise
        return True

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._s3.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)

    def get(self, key: str) -> tuple[bytes, str] | None:
        from botocore.exceptions import ClientError

        try:
            obj = self._s3.get_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return None
            raise
        body: bytes = obj["Body"].read()
        return body, str(obj.get("ContentType") or _content_type(key))

    def url(self, key: str) -> str:
        return f"{self._base}/{key}"


def s3_store_from_settings(
    *, endpoint_url: str, bucket: str, access_key_id: str, secret_access_key: str, region: str, base_url: str
) -> S3AudioStore:
    import boto3

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region,
    )
    return S3AudioStore(client=client, bucket=bucket, base_url=base_url)
