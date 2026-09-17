"""Behavior: GET /audio/{key} streams a rendered file from whichever store is
configured, with the right content type and long cache headers, and 404s
an unknown key. No auth, because audio tags cannot send headers."""

import pytest

from rizalai.audio.engines import FakeTTS
from rizalai.audio.render import key_for
from rizalai.audio.routes import get_audio_store
from rizalai.audio.store import LocalAudioStore

pytestmark = pytest.mark.anyio


@pytest.fixture
def local_store(client, tmp_path):
    from rizalai.main import app

    store = LocalAudioStore(tmp_path, base_url="http://test/audio")
    app.dependency_overrides[get_audio_store] = lambda: store
    yield store
    app.dependency_overrides.pop(get_audio_store, None)


async def test_serves_rendered_audio(client, local_store):
    engine = FakeTTS()
    key = key_for(engine, "Pumasok sa sala si Kapitan Tiago.")
    local_store.put(key, engine.synthesize("Pumasok sa sala si Kapitan Tiago."), engine.content_type)

    response = await client.get(f"/audio/{key}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/wav")
    assert "max-age" in response.headers.get("cache-control", "")
    assert response.content[:4] == b"RIFF"


async def test_unknown_key_is_404_and_paths_are_not_traversable(client, local_store):
    assert (await client.get("/audio/nope.wav")).status_code == 404
    assert (await client.get("/audio/..%2F..%2Fetc%2Fpasswd")).status_code in (404, 422)
