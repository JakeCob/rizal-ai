"""Parse Project Gutenberg plain-text editions into passages.

Chunking is by paragraph within a chapter (DECISIONS.md D19), never by token
count. Offsets index into the normalized text (CRLF folded to LF) so a
passage can always be sliced back out of the source file.

Editions verified on 2026-09-17:
- 47584  Noli me tángere, Spanish, Rizal's original (1887)
- 20228  Noli Me Tangere, Tagalog, Pascual H. Poblete translation (1909)
- 6737   The Social Cancer, English, Charles Derbyshire translation (1912)
"""

import re
from dataclasses import dataclass

import httpx

START_MARKER = "*** START"
END_MARKER = "*** END"

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roman_to_int(value: str) -> int:
    total = 0
    prev = 0
    for ch in reversed(value.upper()):
        n = ROMAN[ch]
        total = total - n if n < prev else total + n
        prev = max(prev, n)
    return total


@dataclass(frozen=True)
class EditionSpec:
    key: str
    work: str
    language: str
    translator: str | None
    gutenberg_id: int
    title: str
    heading: re.Pattern[str]
    license_note: str


def _pd(gutenberg_id: int, description: str) -> str:
    return f"Public domain. {description}. Source: https://www.gutenberg.org/ebooks/{gutenberg_id}"


EDITIONS: dict[str, EditionSpec] = {
    "noli_es": EditionSpec(
        key="noli_es",
        work="noli",
        language="es",
        translator=None,
        gutenberg_id=47584,
        title="Noli me tángere (1887)",
        # A roman numeral alone on a line, preceded by a blank line, then a
        # blank line and an uppercase title. The uppercase requirement keeps
        # footnote cross references such as "capítulo\nXLVI." out.
        heading=re.compile(r"(?m)(?<=\n\n)([IVXLC]+)\n\n+([A-ZÁÉÍÓÚÑÜ«¡¿][^\n]*)\n"),
        license_note=_pd(47584, "José Rizal, Noli me tángere, Spanish original, first published 1887"),
    ),
    "noli_tl": EditionSpec(
        key="noli_tl",
        work="noli",
        language="tl",
        translator="poblete_1909",
        gutenberg_id=20228,
        title="Noli Me Tangere, Tagalog translation by Pascual H. Poblete (1909)",
        heading=re.compile(r"(?m)^=([IVXLC]+)\.?=\n+=([^\n=]+)=\n"),
        license_note=_pd(20228, "Pascual H. Poblete's Tagalog translation, Manila 1909"),
    ),
    "noli_en": EditionSpec(
        key="noli_en",
        work="noli",
        language="en",
        translator="derbyshire_1912",
        gutenberg_id=6737,
        title="The Social Cancer, English translation by Charles Derbyshire (1912)",
        heading=re.compile(r"(?m)^CHAPTER ([IVXLC]+)\n+([^\n]+)\n"),
        license_note=_pd(6737, "Charles Derbyshire's English translation, Manila 1912"),
    ),
}


@dataclass(frozen=True)
class ParsedPassage:
    work: str
    language: str
    translator: str | None
    chapter: int
    chapter_title: str
    paragraph_index: int
    text: str
    char_start: int
    char_end: int
    is_footnote: bool


_PARAGRAPH = re.compile(r"(?:[^\n]*\S[^\n]*)(?:\n[^\n]*\S[^\n]*)*")
_FOOTNOTE = re.compile(r"^\[\d+\]")


def normalize(raw: str) -> str:
    return raw.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")


def body_bounds(text: str) -> tuple[int, int]:
    start = text.find(START_MARKER)
    body_start = text.find("\n", start) + 1 if start >= 0 else 0
    end = text.find(END_MARKER, body_start)
    body_end = end if end >= 0 else len(text)
    return body_start, body_end


def parse_edition(spec: EditionSpec, raw: str) -> list[ParsedPassage]:
    text = normalize(raw)
    body_start, body_end = body_bounds(text)
    headings = list(spec.heading.finditer(text, body_start, body_end))
    passages: list[ParsedPassage] = []
    for i, match in enumerate(headings):
        chapter = roman_to_int(match.group(1))
        title = match.group(2).strip().strip("=").strip()
        seg_start = match.end()
        seg_end = headings[i + 1].start() if i + 1 < len(headings) else body_end
        index = 0
        for para in _PARAGRAPH.finditer(text, seg_start, seg_end):
            clean = " ".join(para.group(0).split())
            if not clean:
                continue
            index += 1
            passages.append(
                ParsedPassage(
                    work=spec.work,
                    language=spec.language,
                    translator=spec.translator,
                    chapter=chapter,
                    chapter_title=title,
                    paragraph_index=index,
                    text=clean,
                    char_start=para.start(),
                    char_end=para.end(),
                    is_footnote=bool(_FOOTNOTE.match(clean)),
                )
            )
    return passages


def gutenberg_text_url(gutenberg_id: int) -> str:
    return f"https://www.gutenberg.org/cache/epub/{gutenberg_id}/pg{gutenberg_id}.txt"


def fetch_gutenberg_text(gutenberg_id: int, client: httpx.Client | None = None) -> str:
    headers = {"User-Agent": "rizalai-ingest/0.1 (+https://github.com/JakeCob/rizal-ai)"}
    http = client or httpx.Client(timeout=120.0, follow_redirects=True, headers=headers)
    response = http.get(gutenberg_text_url(gutenberg_id))
    response.raise_for_status()
    return response.text
