"""Behaviors for the S3-compatible audio store (Railway buckets, D33):
- exists issues head_object and maps 404 to False
- put issues put_object with the content type
- get returns the object bytes and content type, None when missing
- the URL is always the API's /audio/{key}, never the bucket's
"""

import boto3
from botocore.stub import ANY, Stubber

from rizalai.audio.store import LocalAudioStore, S3AudioStore


def _store():
    client = boto3.client(
        "s3",
        region_name="auto",
        endpoint_url="https://storage.example.test",
        aws_access_key_id="k",
        aws_secret_access_key="s",
    )
    return S3AudioStore(client=client, bucket="audio", base_url="https://api.example.test/audio"), Stubber(
        client
    )


def test_exists_maps_head_object():
    store, stub = _store()
    stub.add_response("head_object", {"ContentLength": 3}, {"Bucket": "audio", "Key": "a.wav"})
    stub.add_client_error("head_object", "404", expected_params={"Bucket": "audio", "Key": "b.wav"})
    with stub:
        assert store.exists("a.wav") is True
        assert store.exists("b.wav") is False


def test_put_and_get():
    store, stub = _store()
    stub.add_response(
        "put_object", {}, {"Bucket": "audio", "Key": "a.wav", "Body": b"RIFF", "ContentType": "audio/wav"}
    )
    with stub:
        store.put("a.wav", b"RIFF", "audio/wav")

    from io import BytesIO

    store, stub = _store()
    stub.add_response(
        "get_object",
        {"Body": BytesIO(b"RIFF"), "ContentType": "audio/wav"},
        {"Bucket": "audio", "Key": "a.wav"},
    )
    stub.add_client_error("get_object", "NoSuchKey", expected_params={"Bucket": "audio", "Key": ANY})
    with stub:
        got = store.get("a.wav")
        assert got == (b"RIFF", "audio/wav")
        assert store.get("missing.wav") is None


def test_urls_point_at_the_api(tmp_path):
    store, _ = _store()
    assert store.url("a.wav") == "https://api.example.test/audio/a.wav"
    local = LocalAudioStore(tmp_path, base_url="http://localhost:8000/audio")
    local.put("a.wav", b"RIFF", "audio/wav")
    assert local.get("a.wav") == (b"RIFF", "audio/wav")
    assert local.get("nope.mp3") is None
    assert local.url("a.wav") == "http://localhost:8000/audio/a.wav"
