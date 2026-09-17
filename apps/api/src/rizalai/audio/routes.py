"""GET /audio/{key}: rendered audio from whichever store is configured.
No auth, because audio elements cannot send headers. Keys are content
hashes, so the response is immutable and cached for a year."""

import re
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from rizalai.audio.store import AudioStore, LocalAudioStore, s3_store_from_settings
from rizalai.config import get_settings

router = APIRouter(tags=["audio"])

KEY = re.compile(r"^[a-f0-9]{16}\.(wav|mp3)$")


@lru_cache
def _store() -> AudioStore:
    settings = get_settings()
    if settings.audio_store == "s3":
        return s3_store_from_settings(
            endpoint_url=settings.s3_endpoint_url,
            bucket=settings.s3_bucket,
            access_key_id=settings.s3_access_key_id,
            secret_access_key=settings.s3_secret_access_key,
            region=settings.s3_region,
            base_url=settings.audio_base_url,
        )
    return LocalAudioStore(settings.audio_local_dir, settings.audio_base_url)


def get_audio_store() -> AudioStore:
    """FastAPI dependency and the CLI's store. Overridden in tests."""
    return _store()


@router.get("/audio/{key}")
async def get_audio(key: str, store: Annotated[AudioStore, Depends(get_audio_store)]) -> Response:
    if not KEY.match(key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    found = store.get(key)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    data, content_type = found
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
