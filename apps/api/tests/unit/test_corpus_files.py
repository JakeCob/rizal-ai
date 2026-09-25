"""Behaviors (plan 007, D37):
- Given the three committed Gutenberg texts, then each exists under the name
  `rizalai ingest` and `rizalai bootstrap` look for, and matches its pinned
  sha256, so production passages are byte-identical to dev's and the hand
  alignment of pinned refs cannot drift under a fresh download.
- Given `rizalai ingest` without --file, then it reads the committed file and
  checks its digest; a missing or changed file is refused, and a download
  happens only with --download, into a file that is not the pinned name.
"""

import hashlib
from pathlib import Path

import pytest

from rizalai.corpus import ingest
from rizalai.corpus.gutenberg import EDITIONS
from rizalai.corpus.ingest import RAW_DIR, RAW_FILES, RAW_SHA256, CorpusFileError, load_edition_text, raw_path

API_ROOT = Path(__file__).resolve().parents[2]

PINNED = {
    "noli_es": ("noli_es_rizal_1887.txt", "a1e437097e5c6b86baa0db08c3d091b76d46f347db5f1e1dd14bdfb1d3f84f8e"),
    "noli_tl": (
        "noli_tl_poblete_1909.txt",
        "43ef048e077f5a4080f6887b36ea26328ae1ce192891a20f28bf58909b06119a",
    ),
    "noli_en": (
        "noli_en_derbyshire_1912.txt",
        "edaff46d61e92a7eeea5236280d2c9db7a304210379fa2d65148d097ad02b59e",
    ),
}


def test_every_edition_has_a_pinned_file():
    assert set(RAW_FILES) == set(EDITIONS) == set(PINNED)
    assert {k: (RAW_FILES[k], RAW_SHA256[k]) for k in PINNED} == PINNED


@pytest.mark.parametrize("key", sorted(PINNED))
def test_committed_text_matches_its_digest(key):
    path = API_ROOT / raw_path(key)
    assert path == API_ROOT / RAW_DIR / PINNED[key][0]
    assert path.is_file(), f"missing {path}"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == PINNED[key][1]
    assert "*** START OF" in path.read_text(encoding="utf-8", errors="replace")  # license header kept


def test_ingest_reads_the_committed_file_after_checking_its_digest():
    text = load_edition_text("noli_tl", raw_dir=API_ROOT / RAW_DIR)
    assert "Noli" in text


def test_ingest_refuses_a_missing_file_without_download(tmp_path):
    with pytest.raises(CorpusFileError, match="--download"):
        load_edition_text("noli_tl", raw_dir=tmp_path)


def test_ingest_refuses_a_changed_file(tmp_path):
    (tmp_path / RAW_FILES["noli_tl"]).write_text("not the pinned text", encoding="utf-8")
    with pytest.raises(CorpusFileError, match="sha256"):
        load_edition_text("noli_tl", raw_dir=tmp_path)


def test_download_goes_to_a_separate_file(tmp_path, monkeypatch):
    monkeypatch.setattr(ingest, "fetch_gutenberg_text", lambda gutenberg_id: f"fresh text {gutenberg_id}")
    text = load_edition_text("noli_tl", raw_dir=tmp_path, download=True)
    assert text == "fresh text 20228"
    assert not (tmp_path / RAW_FILES["noli_tl"]).exists()
    assert (tmp_path / "noli_tl.download.txt").read_text(encoding="utf-8") == text


def test_an_explicit_file_is_read_as_given(tmp_path):
    path = tmp_path / "mine.txt"
    path.write_text("my own copy", encoding="utf-8")
    assert load_edition_text("noli_tl", file=path) == "my own copy"
