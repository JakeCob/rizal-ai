"""Behaviors for pre-rendered audio (DECISIONS.md D12):
- the audio key is a content hash of engine, voice, and text, so the same
  line renders once and a changed line renders again
- the fake engine returns bytes without a network
- the local store writes, reports existence, and yields a URL
- rendering a set of lines skips keys the store already has
- the bake-off renders every line with every available engine into a
  samples folder, one file per engine per line
- the seed fills audio_url on beats and listen_tap exercises when the store
  has the rendered file, and leaves null otherwise
"""

from pathlib import Path

from rizalai.audio.engines import FakeTTS, available_engines
from rizalai.audio.render import audio_key, bakeoff, render_lines
from rizalai.audio.store import LocalAudioStore


def test_audio_key_is_content_hash():
    a = audio_key("fake", "default", "Pumasok sa sala si Kapitan Tiago.")
    assert a == audio_key("fake", "default", "Pumasok sa sala si Kapitan Tiago.")
    assert a != audio_key("fake", "default", "Pumasok sa sala si Kapitan Tiago")
    assert a != audio_key("mms", "default", "Pumasok sa sala si Kapitan Tiago.")
    assert a.endswith(".wav") and len(a) == 16 + 4


def test_fake_engine_renders_bytes_deterministically():
    engine = FakeTTS()
    out = engine.synthesize("Kumain kayo sa amin bukas.")
    assert out.startswith(b"RIFF")
    assert out == engine.synthesize("Kumain kayo sa amin bukas.")
    assert engine.name == "fake" and engine.extension == "wav"


def test_local_store_put_exists_url(tmp_path: Path):
    store = LocalAudioStore(tmp_path, base_url="/audio")
    assert store.exists("abc.wav") is False
    store.put("abc.wav", b"RIFF....", content_type="audio/wav")
    assert store.exists("abc.wav") is True
    assert store.url("abc.wav") == "/audio/abc.wav"
    assert (tmp_path / "abc.wav").read_bytes() == b"RIFF...."


def test_render_lines_skips_existing(tmp_path: Path):
    store = LocalAudioStore(tmp_path, base_url="/audio")
    engine = FakeTTS()
    lines = ["Isa.", "Dalawa.", "Isa."]
    report = render_lines(lines, engine, store)
    assert report.rendered == 2 and report.skipped == 1
    again = render_lines(lines, engine, store)
    assert again.rendered == 0 and again.skipped == 3
    assert len(list(tmp_path.iterdir())) == 2


def test_bakeoff_writes_one_file_per_engine_per_line(tmp_path: Path):
    engines = [FakeTTS(), FakeTTS(name="fake2")]
    written = bakeoff(["Isa.", "Dalawa."], engines, tmp_path)
    assert len(written) == 4
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["fake-01.wav", "fake-02.wav", "fake2-01.wav", "fake2-02.wav"]
    assert (tmp_path / "README.md").exists() is False


def test_available_engines_always_includes_fake():
    names = [e.name for e in available_engines(settings=None)]
    assert "fake" in names
