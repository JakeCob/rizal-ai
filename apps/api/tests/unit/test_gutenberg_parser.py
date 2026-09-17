"""Behaviors:
- Given a Gutenberg plain-text file, when parsed, then the header and
  footer are dropped and chapters are detected by the edition's heading
  pattern, numbered from roman numerals.
- Given a chapter, when split, then paragraphs are numbered from 1 and the
  char offsets slice the normalized text back to the paragraph.
- Given the Tagalog edition, when parsed, then footnote paragraphs are
  flagged and chapter titles are stripped of the = markers.
- Given text before the first heading, then it is not a chapter.
"""

from pathlib import Path

import pytest

from rizalai.corpus.gutenberg import EDITIONS, normalize, parse_edition, roman_to_int

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "gutenberg"


@pytest.mark.parametrize(
    ("roman", "value"), [("I", 1), ("IV", 4), ("IX", 9), ("XLVI", 46), ("LXIII", 63), ("LXIV", 64)]
)
def test_roman_to_int(roman, value):
    assert roman_to_int(roman) == value


@pytest.mark.parametrize("key", ["noli_es", "noli_tl", "noli_en"])
def test_two_chapters_detected_with_expected_paragraph_counts(key):
    raw = (FIXTURES / f"{key}.txt").read_text(encoding="utf-8")
    passages = parse_edition(EDITIONS[key], raw)
    chapters = sorted({p.chapter for p in passages})
    assert chapters == [1, 2]
    by_chapter = {c: [p for p in passages if p.chapter == c] for c in chapters}
    assert len(by_chapter[1]) == 4
    assert len(by_chapter[2]) == 2
    assert [p.paragraph_index for p in by_chapter[1]] == [1, 2, 3, 4]
    assert all(p.work == "noli" for p in passages)
    assert all(p.language == EDITIONS[key].language for p in passages)


@pytest.mark.parametrize("key", ["noli_es", "noli_tl", "noli_en"])
def test_offsets_round_trip_to_paragraph_text(key):
    raw = (FIXTURES / f"{key}.txt").read_text(encoding="utf-8")
    text = normalize(raw)
    for p in parse_edition(EDITIONS[key], raw):
        sliced = text[p.char_start : p.char_end]
        assert " ".join(sliced.split()) == p.text


def test_preface_is_not_a_chapter_and_header_is_dropped():
    raw = (FIXTURES / "noli_en.txt").read_text(encoding="utf-8")
    passages = parse_edition(EDITIONS["noli_en"], raw)
    joined = " ".join(p.text for p in passages)
    assert "Preface paragraph" not in joined
    assert "PROJECT GUTENBERG" not in joined
    assert passages[0].text.startswith("On the last of October")


def test_chapter_titles_captured_and_markers_stripped():
    raw = (FIXTURES / "noli_tl.txt").read_text(encoding="utf-8")
    passages = parse_edition(EDITIONS["noli_tl"], raw)
    assert passages[0].chapter_title == "ISANG PAGCACAPISAN."
    raw_es = (FIXTURES / "noli_es.txt").read_text(encoding="utf-8")
    assert parse_edition(EDITIONS["noli_es"], raw_es)[0].chapter_title == "UNA REUNIÓN"


def test_footnote_paragraphs_are_flagged():
    text = (
        "*** START OF THE PROJECT GUTENBERG EBOOK X ***\n\n=I.=\n\n=TITLE.=\n\nBody paragraph.\n\n"
        "[1] A footnote.--P.H.P.\n\nAnother body paragraph.\n\n*** END OF THE PROJECT GUTENBERG EBOOK X ***\n"
    )
    passages = parse_edition(EDITIONS["noli_tl"], text)
    assert [p.is_footnote for p in passages] == [False, True, False]
    assert [p.paragraph_index for p in passages] == [1, 2, 3]


def test_edition_metadata_is_complete():
    for key, spec in EDITIONS.items():
        assert spec.gutenberg_id > 0, key
        assert spec.license_note.startswith("Public domain"), key
        assert spec.work == "noli"
